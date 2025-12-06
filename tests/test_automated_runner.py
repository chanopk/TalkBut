"""Tests for automated runner functionality."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

from talkbut.scheduling.automated_runner import AutomatedRunner, APIError


class TestAutomatedRunner:
    """Tests for AutomatedRunner class."""
    
    def test_runner_initialization(self):
        """Test that runner can be initialized."""
        runner = AutomatedRunner()
        assert runner is not None
        assert runner.config is None
        assert runner.status_manager is None
    
    def test_runner_initialization_with_config_path(self):
        """Test that runner can be initialized with config path."""
        runner = AutomatedRunner(config_path="/tmp/test_config.yaml")
        assert runner.config_path == "/tmp/test_config.yaml"
    
    @patch('talkbut.scheduling.automated_runner.ConfigManager')
    @patch('talkbut.scheduling.automated_runner.StatusManager')
    def test_load_configuration_success(self, mock_status_manager, mock_config_manager):
        """Test successful configuration loading."""
        # Setup mocks
        mock_config = Mock()
        mock_config.get_schedule_config.return_value = {
            'status_file': './data/schedule_status.json'
        }
        mock_config_manager.return_value = mock_config
        
        # Create runner and load config
        runner = AutomatedRunner()
        result = runner._load_configuration()
        
        # Verify
        assert result is True
        assert runner.config is not None
        assert runner.status_manager is not None
    
    @patch('talkbut.scheduling.automated_runner.ConfigManager')
    def test_load_configuration_failure(self, mock_config_manager):
        """Test configuration loading failure."""
        # Setup mock to raise exception
        mock_config_manager.side_effect = Exception("Config error")
        
        # Create runner and try to load config
        runner = AutomatedRunner()
        result = runner._load_configuration()
        
        # Verify
        assert result is False
        assert runner.config is None
    
    @patch('talkbut.scheduling.automated_runner.GitCollector')
    @patch('talkbut.scheduling.automated_runner.DataParser')
    def test_collect_commits_success(self, mock_parser, mock_collector_class):
        """Test successful commit collection."""
        # Setup mocks
        mock_commit = Mock()
        mock_commit.repo_name = None
        
        mock_collector = Mock()
        mock_collector.collect_commits.return_value = [mock_commit]
        mock_collector_class.return_value = mock_collector
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        # Create runner with mock config
        runner = AutomatedRunner()
        runner.config = Mock()
        runner.config.git_repos = [{'name': 'test_repo', 'path': '/tmp/test'}]
        runner.config.get.return_value = 'test@example.com'
        
        # Collect commits
        success, commits, error = runner._collect_commits('2025-12-07')
        
        # Verify
        assert success is True
        assert commits is not None
        assert len(commits) == 1
        assert error is None
        assert commits[0].repo_name == 'test_repo'
    
    @patch('talkbut.scheduling.automated_runner.GitCollector')
    def test_collect_commits_no_repos(self, mock_collector_class):
        """Test commit collection with no repositories configured."""
        # Create runner with mock config (no repos)
        runner = AutomatedRunner()
        runner.config = Mock()
        runner.config.git_repos = []
        
        # Collect commits
        success, commits, error = runner._collect_commits('2025-12-07')
        
        # Verify
        assert success is False
        assert commits is None
        assert error == "No repositories configured"
    
    @patch('talkbut.scheduling.automated_runner.AIAnalyzer')
    def test_analyze_and_save_success(self, mock_analyzer_class):
        """Test successful analysis and save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup mocks
            mock_report = Mock()
            mock_report.ai_summary = "Test summary"
            mock_report.total_commits = 5
            mock_report.files_changed = 10
            mock_report.insertions = 100
            mock_report.deletions = 50
            mock_report.categories = ["feature", "bugfix"]
            mock_report.tasks = []
            
            mock_analyzer = Mock()
            mock_analyzer.analyze_commits.return_value = mock_report
            mock_analyzer_class.return_value = mock_analyzer
            
            # Create runner with mock config
            runner = AutomatedRunner()
            runner.config = Mock()
            runner.config.get.return_value = tmpdir
            
            # Create mock commits
            mock_commits = [Mock()]
            
            # Analyze and save
            success, error = runner._analyze_and_save(mock_commits, '2025-12-07')
            
            # Verify
            assert success is True
            assert error is None
            
            # Check that file was created
            log_file = Path(tmpdir) / 'daily_log_2025-12-07.json'
            assert log_file.exists()
            
            # Verify content
            with open(log_file, 'r') as f:
                data = json.load(f)
                assert data['date'] == '2025-12-07'
                assert data['summary'] == "Test summary"
                assert data['stats']['commits'] == 5
    
    @patch('talkbut.scheduling.automated_runner.AIAnalyzer')
    def test_analyze_and_save_api_error(self, mock_analyzer_class):
        """Test that API errors are raised as APIError."""
        # Setup mock to raise API error
        mock_analyzer = Mock()
        mock_analyzer.analyze_commits.side_effect = Exception("API rate limit exceeded")
        mock_analyzer_class.return_value = mock_analyzer
        
        # Create runner with mock config
        runner = AutomatedRunner()
        runner.config = Mock()
        runner.config.get.return_value = '/tmp'
        
        # Create mock commits
        mock_commits = [Mock()]
        
        # Analyze and save should raise APIError
        with pytest.raises(APIError):
            runner._analyze_and_save(mock_commits, '2025-12-07')
    
    @patch('talkbut.scheduling.automated_runner.time.sleep')
    def test_run_with_retry_success_first_attempt(self, mock_sleep):
        """Test successful run on first attempt."""
        runner = AutomatedRunner()
        
        # Mock all dependencies
        runner._load_configuration = Mock(return_value=True)
        runner._collect_commits = Mock(return_value=(True, [Mock()], None))
        runner._analyze_and_save = Mock(return_value=(True, None))
        runner.status_manager = Mock()
        
        # Run with retry
        exit_code = runner.run_with_retry()
        
        # Verify
        assert exit_code == 0
        runner.status_manager.record_run.assert_called_once_with(success=True)
        mock_sleep.assert_not_called()  # No retries needed
    
    @patch('talkbut.scheduling.automated_runner.time.sleep')
    def test_run_with_retry_api_error_then_success(self, mock_sleep):
        """Test retry logic with API error then success."""
        runner = AutomatedRunner()
        
        # Mock configuration and status manager
        runner._load_configuration = Mock(return_value=True)
        runner.status_manager = Mock()
        runner.config = Mock()
        runner.config.get_schedule_config.return_value = {
            'error_log': '/tmp/test_error.log'
        }
        
        # Mock collect commits to succeed
        runner._collect_commits = Mock(return_value=(True, [Mock()], None))
        
        # Mock analyze to fail once with API error, then succeed
        runner._analyze_and_save = Mock(side_effect=[
            APIError("API timeout"),
            (True, None)
        ])
        
        # Run with retry
        exit_code = runner.run_with_retry()
        
        # Verify
        assert exit_code == 0
        runner.status_manager.record_run.assert_called_once_with(success=True)
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second backoff
    
    @patch('talkbut.scheduling.automated_runner.time.sleep')
    @patch('talkbut.scheduling.automated_runner.log_error')
    def test_run_with_retry_all_attempts_fail(self, mock_log_error, mock_sleep):
        """Test that all retry attempts are exhausted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = AutomatedRunner()
            
            # Mock configuration and status manager
            runner._load_configuration = Mock(return_value=True)
            runner.status_manager = Mock()
            runner.config = Mock()
            runner.config.get_schedule_config.return_value = {
                'error_log': f'{tmpdir}/test_error.log'
            }
            
            # Mock collect commits to succeed
            runner._collect_commits = Mock(return_value=(True, [Mock()], None))
            
            # Mock analyze to always fail with API error
            runner._analyze_and_save = Mock(side_effect=APIError("API error"))
            
            # Run with retry
            exit_code = runner.run_with_retry(max_retries=3)
            
            # Verify
            assert exit_code == 1
            runner.status_manager.record_run.assert_called_once()
            call_args = runner.status_manager.record_run.call_args
            assert call_args[1]['success'] is False
            
            # Verify exponential backoff was used
            assert mock_sleep.call_count == 2  # 2 retries (not on last attempt)
            mock_sleep.assert_any_call(1)  # 2^0
            mock_sleep.assert_any_call(2)  # 2^1
    
    @patch('talkbut.scheduling.automated_runner.time.sleep')
    def test_run_with_retry_no_commits(self, mock_sleep):
        """Test successful run when no commits found."""
        runner = AutomatedRunner()
        
        # Mock all dependencies
        runner._load_configuration = Mock(return_value=True)
        runner._collect_commits = Mock(return_value=(True, [], None))  # No commits
        runner.status_manager = Mock()
        
        # Run with retry
        exit_code = runner.run_with_retry()
        
        # Verify
        assert exit_code == 0
        runner.status_manager.record_run.assert_called_once_with(success=True)
        mock_sleep.assert_not_called()
    
    def test_run_with_retry_config_load_failure(self):
        """Test that config load failure returns error code."""
        runner = AutomatedRunner()
        
        # Mock configuration to fail
        runner._load_configuration = Mock(return_value=False)
        
        # Run with retry
        exit_code = runner.run_with_retry()
        
        # Verify
        assert exit_code == 1

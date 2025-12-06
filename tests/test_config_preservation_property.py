"""Property-based tests for configuration preservation in automated execution.

**Feature: automated-daily-logging, Property 2: Configuration parameters are preserved in automated execution**
**Validates: Requirements 1.3**
"""

import pytest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume

from talkbut.core.config import ConfigManager
from talkbut.scheduling.scheduler_manager import SchedulerManager


# Strategy for generating valid configuration parameters
@st.composite
def config_parameters(draw):
    """Generate valid configuration parameters."""
    # Generate author (email or name)
    author_choice = draw(st.integers(min_value=0, max_value=1))
    if author_choice == 0:
        # Email format
        username = draw(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=3, max_size=10))
        domain = draw(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=3, max_size=10))
        author = f"{username}@{domain}.com"
    else:
        # Name format
        author = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=3, max_size=20))
    
    # Generate schedule time
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    schedule_time = f"{hour:02d}:{minute:02d}"
    
    # Generate repository paths (simplified for testing)
    num_repos = draw(st.integers(min_value=1, max_value=3))
    repositories = []
    for i in range(num_repos):
        repo_name = draw(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=3, max_size=10))
        repositories.append({
            'name': repo_name,
            'path': f'/tmp/test_repo_{repo_name}'
        })
    
    return {
        'author': author,
        'schedule_time': schedule_time,
        'repositories': repositories
    }


class TestConfigurationPreservationProperties:
    """Property-based tests for configuration preservation."""
    
    @given(params=config_parameters())
    @settings(max_examples=100, deadline=None)
    def test_property_config_parameters_preserved_in_command(self, params):
        """
        Property 2: Configuration parameters are preserved in automated execution.
        
        For any configuration (author, repositories, schedule time), when automated
        logging executes, the parameters used should match the configuration file values.
        
        This test verifies that the command built by SchedulerManager will use the
        configuration file, ensuring parameters are preserved.
        
        **Feature: automated-daily-logging, Property 2: Configuration parameters are preserved in automated execution**
        **Validates: Requirements 1.3**
        """
        # Create a temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'config.yaml')
            
            # Write configuration to file
            config_data = {
                'git': {
                    'author': params['author'],
                    'repositories': params['repositories']
                },
                'schedule': {
                    'enabled': True,
                    'time': params['schedule_time']
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Mock platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                from talkbut.scheduling.platform_detector import SchedulerType
                mock_detect.return_value = SchedulerType.CRON
                
                # Create SchedulerManager
                manager = SchedulerManager()
                
                # Mock the scheduler to capture the command
                mock_scheduler = Mock()
                mock_scheduler.create_job = Mock(return_value=True)
                manager.scheduler = mock_scheduler
                
                # Enable scheduling with the config path
                result = manager.enable(params['schedule_time'], config_path)
                
                # Verify enable succeeded
                assert result is True, "Enable operation should succeed"
                
                # Property: The command should reference the config file
                # This ensures that when the scheduled task runs, it will load
                # the configuration from the file, preserving all parameters
                mock_scheduler.create_job.assert_called_once()
                call_args = mock_scheduler.create_job.call_args
                
                # Extract the command that was passed
                command = call_args[0][1]  # Second argument is the command
                
                # Verify the command includes the config path
                assert config_path in command, \
                    f"Command should include config path {config_path}, got: {command}"
                
                # Verify the command includes the automated_runner (which handles logging)
                assert "automated_runner" in command, \
                    f"Command should include 'automated_runner' module, got: {command}"
    
    @given(params=config_parameters())
    @settings(max_examples=100, deadline=None)
    def test_property_config_loaded_correctly_from_file(self, params):
        """
        Property 2: Configuration parameters are preserved in automated execution.
        
        For any configuration written to a file, loading that configuration should
        return the exact same parameters that were written.
        
        This verifies the round-trip: write config -> load config -> parameters match.
        
        **Feature: automated-daily-logging, Property 2: Configuration parameters are preserved in automated execution**
        **Validates: Requirements 1.3**
        """
        # Create a temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'config.yaml')
            
            # Write configuration to file
            config_data = {
                'git': {
                    'author': params['author'],
                    'repositories': params['repositories']
                },
                'schedule': {
                    'enabled': True,
                    'time': params['schedule_time']
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Set environment variable to point to our test config
            original_env = os.environ.get('TALKBUT_CONFIG_PATH')
            try:
                os.environ['TALKBUT_CONFIG_PATH'] = config_path
                
                # Clear the singleton instance to force reload
                ConfigManager._instance = None
                
                # Load configuration
                config = ConfigManager()
                
                # Property: Loaded parameters should match what was written
                loaded_author = config.get('git.author')
                loaded_repos = config.get('git.repositories')
                loaded_schedule = config.get_schedule_config()
                
                assert loaded_author == params['author'], \
                    f"Loaded author '{loaded_author}' should match written author '{params['author']}'"
                
                assert loaded_repos == params['repositories'], \
                    f"Loaded repositories should match written repositories"
                
                assert loaded_schedule['time'] == params['schedule_time'], \
                    f"Loaded schedule time '{loaded_schedule['time']}' should match written time '{params['schedule_time']}'"
                
                assert loaded_schedule['enabled'] is True, \
                    "Loaded schedule enabled should be True"
                
            finally:
                # Restore original environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                
                # Clear singleton for next test
                ConfigManager._instance = None
    
    @given(params=config_parameters())
    @settings(max_examples=100, deadline=None)
    def test_property_schedule_config_persistence(self, params):
        """
        Property 2: Configuration parameters are preserved in automated execution.
        
        For any schedule configuration, after saving to file and reloading,
        the schedule parameters should be preserved exactly.
        
        **Feature: automated-daily-logging, Property 2: Configuration parameters are preserved in automated execution**
        **Validates: Requirements 1.3**
        """
        # Create a temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'config.yaml')
            
            # Set environment variable to point to our test config
            original_env = os.environ.get('TALKBUT_CONFIG_PATH')
            try:
                os.environ['TALKBUT_CONFIG_PATH'] = config_path
                
                # Clear the singleton instance
                ConfigManager._instance = None
                
                # Create config and set schedule parameters
                config = ConfigManager()
                config.set_schedule_config(
                    enabled=True,
                    time=params['schedule_time']
                )
                
                # Also set git author
                if 'git' not in config._config:
                    config._config['git'] = {}
                config._config['git']['author'] = params['author']
                config._config['git']['repositories'] = params['repositories']
                
                # Save configuration
                config.save_schedule_config(config_path)
                
                # Clear singleton and reload
                ConfigManager._instance = None
                config_reloaded = ConfigManager()
                
                # Property: Reloaded parameters should match what was saved
                reloaded_schedule = config_reloaded.get_schedule_config()
                reloaded_author = config_reloaded.get('git.author')
                reloaded_repos = config_reloaded.get('git.repositories')
                
                assert reloaded_schedule['time'] == params['schedule_time'], \
                    f"Reloaded schedule time '{reloaded_schedule['time']}' should match saved time '{params['schedule_time']}'"
                
                assert reloaded_schedule['enabled'] is True, \
                    "Reloaded schedule enabled should be True"
                
                assert reloaded_author == params['author'], \
                    f"Reloaded author '{reloaded_author}' should match saved author '{params['author']}'"
                
                assert reloaded_repos == params['repositories'], \
                    f"Reloaded repositories should match saved repositories"
                
            finally:
                # Restore original environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                
                # Clear singleton
                ConfigManager._instance = None
    
    @given(params1=config_parameters(), params2=config_parameters())
    @settings(max_examples=50, deadline=None)
    def test_property_config_updates_preserve_other_parameters(self, params1, params2):
        """
        Property 2: Configuration parameters are preserved in automated execution.
        
        For any two configurations, when updating schedule parameters,
        other configuration parameters (like author and repositories) should
        remain unchanged.
        
        **Feature: automated-daily-logging, Property 2: Configuration parameters are preserved in automated execution**
        **Validates: Requirements 1.3**
        """
        # Skip if schedule times are the same (not interesting for update test)
        assume(params1['schedule_time'] != params2['schedule_time'])
        
        # Create a temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'config.yaml')
            
            # Set environment variable
            original_env = os.environ.get('TALKBUT_CONFIG_PATH')
            try:
                os.environ['TALKBUT_CONFIG_PATH'] = config_path
                
                # Clear singleton
                ConfigManager._instance = None
                
                # Create initial configuration
                config = ConfigManager()
                config.set_schedule_config(
                    enabled=True,
                    time=params1['schedule_time']
                )
                config._config['git'] = {
                    'author': params1['author'],
                    'repositories': params1['repositories']
                }
                config.save_schedule_config(config_path)
                
                # Clear and reload
                ConfigManager._instance = None
                config = ConfigManager()
                
                # Update only schedule time
                config.set_schedule_config(time=params2['schedule_time'])
                config.save_schedule_config(config_path)
                
                # Clear and reload again
                ConfigManager._instance = None
                config_final = ConfigManager()
                
                # Property: Git parameters should be preserved, schedule time should be updated
                final_schedule = config_final.get_schedule_config()
                final_author = config_final.get('git.author')
                final_repos = config_final.get('git.repositories')
                
                # Schedule time should be updated
                assert final_schedule['time'] == params2['schedule_time'], \
                    f"Schedule time should be updated to '{params2['schedule_time']}', got '{final_schedule['time']}'"
                
                # Git parameters should be preserved from params1
                assert final_author == params1['author'], \
                    f"Author should be preserved as '{params1['author']}', got '{final_author}'"
                
                assert final_repos == params1['repositories'], \
                    f"Repositories should be preserved"
                
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                
                # Clear singleton
                ConfigManager._instance = None

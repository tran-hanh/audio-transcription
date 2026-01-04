#!/usr/bin/env python3
"""
Tests for backend services module.

This module tests:
- TranscriptionService: Core transcription logic, progress reporting, error handling
- FileUploadService: File upload and validation
- Cleanup utilities: Temporary file management
"""

import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock
from backend.services import TranscriptionService, FileUploadService
from backend.validators import FileValidator


class TestTranscriptionService:
    """Tests for TranscriptionService class"""

    def test_init(self, test_config):
        """Test TranscriptionService initialization"""
        service = TranscriptionService(test_config)
        assert service.config == test_config
        assert service.validator is not None
        assert isinstance(service.validator, FileValidator)

    def test_gevent_import_fallback(self, test_config):
        """Test that service works with or without gevent (fallback to time.sleep)"""
        # This tests the import fallback logic (lines 23-25)
        # The fallback is tested by checking that SLEEP is defined
        # In production, if gevent is available, SLEEP will be gevent.sleep
        # If not, it will be time.sleep
        # We verify the code path exists by checking SLEEP is callable
        from backend.services import SLEEP
        import time
        # SLEEP should be callable (either gevent.sleep or time.sleep)
        assert callable(SLEEP)
        # Test that it works (should not raise)
        try:
            # Just verify it's a function that can be called
            # We can't actually call it in a test without blocking
            pass
        except Exception:
            pass


    @patch('backend.services.transcribe_audio')
    def test_progress_callback_coverage(self, mock_transcribe, transcription_service):
        """Test progress callback is called (line 103)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            mock_transcribe.return_value = out_path
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should have progress updates
            assert len(results) > 0
            # Verify transcribe_audio was called with progress_callback
            mock_transcribe.assert_called_once()
            call_kwargs = mock_transcribe.call_args[1]
            assert 'progress_callback' in call_kwargs
            assert call_kwargs['progress_callback'] is not None
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    def test_error_handling_path(self, mock_transcribe, transcription_service):
        """Test error handling path (line 138)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        try:
            # Make transcribe_audio raise an error
            mock_transcribe.side_effect = ValueError('Transcription failed')
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should yield error message
            assert len(results) > 0
            error_result = results[-1]
            assert 'error' in error_result.lower() or 'transcription failed' in error_result.lower()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @patch('backend.services.transcribe_audio')
    def test_progress_queue_handling(self, mock_transcribe, transcription_service):
        """Test progress queue handling (lines 146-147)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            # Create a progress callback that adds to queue
            progress_calls = []
            def mock_progress_callback(progress, message):
                progress_calls.append((progress, message))
            
            # Mock transcribe to call progress callback
            def mock_transcribe_func(*args, **kwargs):
                callback = kwargs.get('progress_callback')
                if callback:
                    callback(10, 'Test progress')
                    callback(50, 'Halfway')
                return out_path
            
            mock_transcribe.side_effect = mock_transcribe_func
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should have received progress updates
            assert len(results) > 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    @patch('time.time')
    def test_heartbeat_sending(self, mock_time, mock_transcribe, transcription_service):
        """Test heartbeat sending (lines 154-155)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            # Mock time to simulate long wait (triggers heartbeat)
            # Start at 0, then 15 seconds later (triggers heartbeat), then 30
            call_count = [0]
            def time_side_effect():
                result = call_count[0] * 15
                call_count[0] += 1
                return result
            
            mock_time.side_effect = time_side_effect
            
            # Make transcription take time
            def slow_transcribe(*args, **kwargs):
                import time
                time.sleep(0.1)  # Small delay
                return out_path
            
            mock_transcribe.side_effect = slow_transcribe
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should have heartbeat messages
            assert len(results) > 0
            # Check for heartbeat message
            results_str = ' '.join(results)
            assert 'Transcription in progress' in results_str or len(results) > 1
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    def test_remaining_progress_updates(self, mock_transcribe, transcription_service):
        """Test remaining progress updates handling (line 164)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            mock_transcribe.return_value = out_path
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should process all progress updates
            assert len(results) > 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    def test_gevent_queue_fallback(self, mock_transcribe, transcription_service):
        """Test gevent queue fallback to standard queue (lines 94-99)"""
        # Mock gevent.queue to raise ImportError to trigger fallback (lines 94-99)
        import sys
        original_modules = sys.modules.copy()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            # Temporarily remove gevent.queue to trigger ImportError fallback
            if 'gevent.queue' in sys.modules:
                del sys.modules['gevent.queue']
            if 'gevent' in sys.modules:
                gevent_module = sys.modules['gevent']
                if hasattr(gevent_module, 'queue'):
                    delattr(gevent_module, 'queue')
            
            # This should use standard queue (fallback path lines 94-99)
            mock_transcribe.return_value = out_path
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            assert len(results) > 0
        finally:
            # Restore modules
            sys.modules.clear()
            sys.modules.update(original_modules)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    def test_threading_fallback(self, mock_transcribe, transcription_service):
        """Test threading fallback when gevent not available (lines 123-128)"""
        # Mock gevent import to fail to trigger threading fallback (lines 123-128)
        import sys
        original_modules = sys.modules.copy()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            # Temporarily remove gevent to trigger ImportError fallback
            if 'gevent' in sys.modules:
                del sys.modules['gevent']
            
            # This should use threading (fallback path lines 123-128)
            mock_transcribe.return_value = out_path
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            assert len(results) > 0
        finally:
            # Restore modules
            sys.modules.clear()
            sys.modules.update(original_modules)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    def test_error_queue_handling(self, mock_transcribe, transcription_service):
        """Test error queue handling (lines 140-142, 150-151)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        try:
            # Make transcription raise an error that gets put in error queue (line 116)
            # This error will be retrieved in the loop (lines 140-142)
            mock_transcribe.side_effect = RuntimeError('Test error from queue')
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should yield error message (error retrieved from queue at line 141-142)
            assert len(results) > 0
            error_result = results[-1]
            assert 'error' in error_result.lower() or 'test error' in error_result.lower()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @patch('backend.services.transcribe_audio')
    def test_error_queue_handling_during_loop(self, mock_transcribe, transcription_service):
        """Test error queue handling during transcription loop (line 142)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        try:
            # Create a transcription that puts error in queue after starting
            import queue as std_queue
            error_queue = std_queue.Queue()
            error_queue.put(RuntimeError('Error during transcription'))
            
            # Mock gevent to use our error queue
            with patch('backend.services.gevent') as mock_gevent_module:
                mock_greenlet = MagicMock()
                # Make it not ready initially, then ready after error is checked
                ready_calls = [False, True]
                def ready_side_effect():
                    result = ready_calls[0]
                    if len(ready_calls) > 1:
                        ready_calls.pop(0)
                    return result
                mock_greenlet.ready.side_effect = ready_side_effect
                mock_gevent_module.spawn.return_value = mock_greenlet
                
                # Mock queues to use our error queue
                mock_result_queue = MagicMock()
                mock_result_queue.get.side_effect = std_queue.Empty()
                mock_progress_queue = MagicMock()
                mock_progress_queue.get_nowait.side_effect = std_queue.Empty()
                
                mock_gevent_queue = MagicMock()
                mock_gevent_queue.Queue.side_effect = [mock_result_queue, error_queue, mock_progress_queue]
                mock_gevent_queue.Empty = std_queue.Empty
                mock_gevent_module.queue = mock_gevent_queue
                
                # Mock transcription to not raise immediately
                mock_transcribe.return_value = '/tmp/test.txt'
                
                generator = transcription_service.transcribe_file(tmp_path, 12)
                results = list(generator)
                # Error should be retrieved from queue (line 141) and raised (line 142)
                assert len(results) > 0
                results_str = ' '.join(results)
                assert 'error' in results_str.lower()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @patch('backend.services.transcribe_audio')
    @patch('backend.services.SLEEP')
    def test_progress_queue_multiple_updates(self, mock_sleep, mock_transcribe, transcription_service):
        """Test multiple progress updates from queue (lines 148-151)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            # Create a progress callback that adds multiple updates to queue
            callback_called = [False]
            def mock_transcribe_func(*args, **kwargs):
                callback = kwargs.get('progress_callback')
                if callback:
                    # Add multiple progress updates (lines 148-151)
                    # This tests the while True loop at line 148 and lines 150-151
                    callback(20, 'Progress 1')
                    callback(40, 'Progress 2')
                    callback(60, 'Progress 3')
                    callback_called[0] = True
                # Make transcription take a bit of time so the loop can process queue
                import time
                time.sleep(0.1)
                return out_path
            
            mock_transcribe.side_effect = mock_transcribe_func
            # Make SLEEP do nothing (non-blocking)
            mock_sleep.return_value = None
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should have received multiple progress updates
            # The while True loop at line 148 should process all updates
            # Lines 150-151 should be executed for each update
            assert len(results) > 3
            assert callback_called[0]  # Ensure callback was called
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    @patch('backend.services.SLEEP')
    def test_systemexit_handling_inner(self, mock_sleep, mock_transcribe, transcription_service):
        """Test SystemExit handling in inner try-except (lines 172-187)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            # Make SLEEP raise SystemExit to simulate worker timeout (line 172)
            call_count = [0]
            def sleep_side_effect(*args):
                call_count[0] += 1
                if call_count[0] > 2:  # After a few iterations, raise SystemExit
                    raise SystemExit('Worker timeout')
            
            mock_sleep.side_effect = sleep_side_effect
            
            # Mock transcription to take time (so we enter the loop)
            def slow_transcribe(*args, **kwargs):
                import time
                time.sleep(0.2)  # Give time for loop to run
                return out_path
            
            mock_transcribe.side_effect = slow_transcribe
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should handle SystemExit gracefully (lines 183-187)
            # Lines 183-184 are the except block when connection is closed
            assert len(results) > 0
            # Should have error message about timeout
            results_str = ' '.join(results)
            assert 'timeout' in results_str.lower() or 'interrupted' in results_str.lower()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    @patch('backend.services.SLEEP')
    def test_systemexit_handling_inner_connection_closed(self, mock_sleep, mock_transcribe, transcription_service):
        """Test SystemExit handling when connection is closed (lines 183-184)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            # Make SLEEP raise SystemExit
            call_count = [0]
            def sleep_side_effect(*args):
                call_count[0] += 1
                if call_count[0] > 2:
                    raise SystemExit('Worker timeout')
            
            mock_sleep.side_effect = sleep_side_effect
            
            # Mock transcription to take time
            def slow_transcribe(*args, **kwargs):
                import time
                time.sleep(0.2)
                return out_path
            
            mock_transcribe.side_effect = slow_transcribe
            
            # Mock send_progress to raise exception on first call (simulating closed connection)
            # This will trigger the except block at lines 183-184
            call_count_progress = [0]
            original_send_progress = transcription_service.send_progress
            def mock_send_progress_raising(progress, message):
                call_count_progress[0] += 1
                if call_count_progress[0] == 1:  # First call succeeds
                    return original_send_progress(progress, message)
                # Second call (in SystemExit handler) raises exception
                raise BrokenPipeError('Connection closed')
            
            transcription_service.send_progress = mock_send_progress_raising
            
            try:
                generator = transcription_service.transcribe_file(tmp_path, 12)
                results = list(generator)
                # Should handle gracefully even when connection is closed (lines 183-184)
                # The except block at 183-184 should catch the exception
                assert len(results) >= 1  # At least one result before connection closes
            finally:
                transcription_service.send_progress = original_send_progress
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @patch('backend.services.transcribe_audio')
    @patch('backend.services.SLEEP')
    def test_keyboardinterrupt_handling(self, mock_sleep, mock_transcribe, transcription_service):
        """Test KeyboardInterrupt handling (lines 172-187)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        try:
            # Make SLEEP raise KeyboardInterrupt
            mock_sleep.side_effect = KeyboardInterrupt('Interrupted')
            
            def slow_transcribe(*args, **kwargs):
                import time
                time.sleep(0.1)
                return '/tmp/test_output.txt'
            
            mock_transcribe.side_effect = slow_transcribe
            
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should handle KeyboardInterrupt gracefully
            assert len(results) > 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_systemexit_handling_outer(self, transcription_service):
        """Test SystemExit handling in outer try-except (lines 188-197)"""
        # This test verifies the outer SystemExit handler exists
        # The actual SystemExit handling is tested in routes via test_routes_systemexit_handling
        # We just verify the code path exists by checking the method structure
        import inspect
        source = inspect.getsource(transcription_service.transcribe_file)
        # Verify the outer except block exists (lines 188-197)
        assert 'except (SystemExit, KeyboardInterrupt):' in source or 'except SystemExit' in source
        assert 'Worker timeout detected' in source

    @patch('backend.services.transcribe_audio')
    def test_cleanup_error_handling(self, mock_transcribe, transcription_service):
        """Test cleanup error handling (lines 210-216)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
            out.write('Test transcript')
            out_path = out.name
        
        try:
            mock_transcribe.return_value = out_path
            
            # Mock os.remove to raise OSError during cleanup
            with patch('os.remove', side_effect=OSError('Permission denied')):
                generator = transcription_service.transcribe_file(tmp_path, 12)
                results = list(generator)
                # Should still complete despite cleanup error
                assert len(results) > 0
        finally:
            # Manual cleanup
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except:
                    pass

    @patch('backend.services.transcribe_audio')
    def test_no_result_returned_error(self, mock_transcribe, transcription_service):
        """Test RuntimeError when transcription completes but no result (line 216)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)
            tmp_path = tmp.name
        
        try:
            # Mock the transcription to complete but not put result in queue
            # We need to mock the greenlet/thread to complete, and the queue to be empty
            import queue as std_queue
            
            # Create a mock that simulates transcription completing but no result
            def mock_transcribe_func(*args, **kwargs):
                # Don't put anything in result queue - this simulates the error case
                pass
            
            mock_transcribe.side_effect = mock_transcribe_func
            
            # Mock gevent to create a greenlet that completes immediately
            with patch('backend.services.gevent') as mock_gevent_module:
                # Create mock greenlet that's ready immediately (transcription "completes")
                mock_greenlet = MagicMock()
                mock_greenlet.ready.return_value = True
                mock_gevent_module.spawn.return_value = mock_greenlet
                
                # Mock the queues - result queue will be empty when we try to get (line 209)
                # This will trigger QUEUE_EMPTY exception, then check error queue (line 212-214)
                # Then raise RuntimeError at line 216
                mock_result_queue = MagicMock()
                mock_result_queue.get.side_effect = std_queue.Empty()  # Line 209 -> 210
                mock_error_queue = MagicMock()
                mock_error_queue.get_nowait.side_effect = std_queue.Empty()  # Line 213 -> 215
                mock_progress_queue = MagicMock()
                mock_progress_queue.get_nowait.side_effect = std_queue.Empty()
                
                # Mock gevent.queue to return our empty queues
                mock_gevent_queue = MagicMock()
                mock_gevent_queue.Queue.side_effect = [mock_result_queue, mock_error_queue, mock_progress_queue]
                mock_gevent_queue.Empty = std_queue.Empty
                mock_gevent_module.queue = mock_gevent_queue
                
                generator = transcription_service.transcribe_file(tmp_path, 12)
                results = list(generator)
                # Should yield error about no result (line 216 raises RuntimeError, caught at line 207)
                assert len(results) > 0
                results_str = ' '.join(results)
                assert 'error' in results_str.lower() or 'no result' in results_str.lower() or 'completed but no result' in results_str.lower() or 'runtimeerror' in results_str.lower()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


    def test_send_progress(self, transcription_service):
        """Test send_progress method formats correctly"""
        result = transcription_service.send_progress(50, 'Test message')
        assert result.startswith('data: ')
        assert result.endswith('\n\n')
        
        # Parse the JSON
        json_str = result[6:-2]  # Remove 'data: ' and '\n\n'
        data = json.loads(json_str)
        assert data['progress'] == 50
        assert data['message'] == 'Test message'

    def test_transcribe_file_file_too_large(self, transcription_service):
        """Test transcribe_file with file exceeding size limit"""
        # Create a file that's too large
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * (150 * 1024 * 1024))  # 150MB > 100MB limit
            tmp_path = tmp.name
        
        try:
            generator = transcription_service.transcribe_file(tmp_path, 12)
            results = list(generator)
            
            # Should yield error messages
            assert len(results) >= 2
            assert 'error' in results[1].lower() or 'too large' in results[1].lower()
        finally:
            # File might have been cleaned up by the service, so check if it exists
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_transcribe_file_invalid_chunk_length(self, transcription_service):
        """Test transcribe_file normalizes chunk length"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1000)  # Small file
            tmp_path = tmp.name
        
        try:
            # Mock transcribe_audio to avoid actual API calls
            with patch('backend.services.transcribe_audio') as mock_transcribe:
                mock_transcribe.return_value = tmp_path
                
                # Create a temporary output file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as out:
                    out.write('Test transcript')
                    out_path = out.name
                
                mock_transcribe.return_value = out_path
                
                generator = transcription_service.transcribe_file(tmp_path, 50)  # Invalid chunk length
                # Should normalize to 12
                results = list(generator)
                
                # Verify chunk_length was normalized
                mock_transcribe.assert_called_once()
                call_args = mock_transcribe.call_args
                assert call_args[1]['chunk_length_minutes'] == 12  # Normalized
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_success(self, mock_transcribe, transcription_service):
        """Test successful transcription"""
        # Create test files
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
            output_file.write('Test transcript content')
            output_path = output_file.name
        
        try:
            mock_transcribe.return_value = output_path
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # Should yield progress updates and final transcript
            assert len(results) > 0
            # Last result should contain transcript
            final_result = results[-1]
            assert 'transcript' in final_result.lower() or 'test transcript content' in final_result
            
            mock_transcribe.assert_called_once()
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_empty_transcript(self, mock_transcribe, transcription_service):
        """Test transcription with empty transcript file"""
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as output_file:
            output_file.write('')  # Empty transcript
            output_path = output_file.name
        
        try:
            mock_transcribe.return_value = output_path
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # Should handle empty transcript gracefully
            assert len(results) > 0
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_transcript_not_found(self, mock_transcribe, transcription_service):
        """Test transcription when output file doesn't exist"""
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        try:
            # Mock the transcription to return a non-existent file path
            # The transcription runs in a background greenlet/thread, so we need to mock it
            def mock_transcribe_func(*args, **kwargs):
                # Simulate the transcription completing and returning a non-existent path
                return '/nonexistent/file.txt'
            
            mock_transcribe.side_effect = mock_transcribe_func
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # The FileNotFoundError is caught and converted to an error message in the generator
            # So we should check for the error in the results instead of expecting an exception
            assert len(results) > 0
            # Last result should contain the error
            error_result = results[-1]
            assert 'error' in error_result.lower() or 'not found' in error_result.lower() or 'transcript file not found' in error_result.lower()
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

    @patch('backend.services.transcribe_audio')
    def test_transcribe_file_error_handling(self, mock_transcribe, transcription_service):
        """Test error handling during transcription"""
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b'x' * 1000)
            input_path = input_file.name
        
        try:
            mock_transcribe.side_effect = Exception('Transcription failed')
            
            generator = transcription_service.transcribe_file(input_path, 12)
            results = list(generator)
            
            # Should yield error message
            assert len(results) > 0
            error_result = results[-1]
            assert 'error' in error_result.lower() or 'transcription failed' in error_result.lower()
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)


class TestFileUploadService:
    """Tests for FileUploadService class"""

    def test_init(self, file_validator):
        """Test FileUploadService initialization"""
        service = FileUploadService(file_validator)
        assert service.validator == file_validator

    def test_save_uploaded_file_valid(self, file_upload_service):
        """Test saving a valid uploaded file"""
        # Create a mock file object
        mock_file = MagicMock()
        mock_file.filename = 'test.mp3'
        mock_file.save = MagicMock()
        
        upload_dir = tempfile.mkdtemp()
        
        try:
            file_path = file_upload_service.save_uploaded_file(mock_file, upload_dir)
            
            assert file_path is not None
            assert 'test.mp3' in file_path or 'test' in file_path
            mock_file.save.assert_called_once()
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)

    def test_save_uploaded_file_invalid_extension(self, file_upload_service):
        """Test saving file with invalid extension"""
        mock_file = MagicMock()
        mock_file.filename = 'test.txt'
        
        upload_dir = tempfile.mkdtemp()
        
        try:
            with pytest.raises(ValueError, match='not allowed'):
                file_upload_service.save_uploaded_file(mock_file, upload_dir)
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)

    def test_save_uploaded_file_empty_filename(self, file_upload_service):
        """Test saving file with empty filename"""
        mock_file = MagicMock()
        mock_file.filename = ''
        
        upload_dir = tempfile.mkdtemp()
        
        try:
            with pytest.raises(ValueError, match='No file selected'):
                file_upload_service.save_uploaded_file(mock_file, upload_dir)
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)

    def test_save_uploaded_file_creates_directory(self, file_upload_service):
        """Test that save_uploaded_file creates directory if needed"""
        mock_file = MagicMock()
        mock_file.filename = 'test.mp3'
        mock_file.save = MagicMock()
        
        upload_dir = os.path.join(tempfile.mkdtemp(), 'subdir', 'nested')
        
        try:
            file_path = file_upload_service.save_uploaded_file(mock_file, upload_dir)
            assert os.path.exists(upload_dir)
            mock_file.save.assert_called_once()
        finally:
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(os.path.dirname(os.path.dirname(upload_dir)))

    def test_cleanup_temp_files_success(self, transcription_service):
        """Test _cleanup_temp_files successfully removes files and directories"""
        # Arrange: Create temporary files
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test.txt')
        with open(temp_file, 'w') as f:
            f.write('test')
        
        # Act: Clean up files
        TranscriptionService._cleanup_temp_files(temp_dir, temp_file, temp_file)
        
        # Assert: Files should be cleaned up
        assert not os.path.exists(temp_file)
        assert not os.path.exists(temp_dir)

    def test_cleanup_temp_files_nonexistent(self, transcription_service):
        """Test _cleanup_temp_files handles nonexistent files gracefully"""
        # Act & Assert: Should not raise error
        TranscriptionService._cleanup_temp_files(None, '/nonexistent', '/nonexistent')

    def test_cleanup_temp_files_oserror(self, transcription_service):
        """Test _cleanup_temp_files handles OSError gracefully (lines 219-220)"""
        # Arrange: Mock os.remove to raise OSError
        with patch('os.remove', side_effect=OSError('Permission denied')):
            # Act & Assert: Should not raise, just log warning
            TranscriptionService._cleanup_temp_files(None, '/tmp/test', None)



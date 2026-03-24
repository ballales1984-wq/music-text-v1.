"""
Test per job_status_redis.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestJobStatusRedis:
    """Test per il manager job status Redis."""
    
    @patch('job_status_redis.redis.Redis')
    def test_set_job_status(self, mock_redis):
        """Test salvataggio stato job."""
        from job_status_redis import JobStatusRedis
        
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        
        manager = JobStatusRedis()
        manager._redis = mock_redis_instance
        manager._use_redis = True
        
        manager.set("test-job-123", {"status": "processing", "progress": 50})
        
        mock_redis_instance.setex.assert_called_once()
    
    @patch('job_status_redis.redis.Redis')
    def test_get_job_status(self, mock_redis):
        """Test recupero stato job."""
        from job_status_redis import JobStatusRedis
        
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = json.dumps({
            "status": "completed",
            "progress": 100
        })
        
        manager = JobStatusRedis()
        manager._redis = mock_redis_instance
        manager._use_redis = True
        
        result = manager.get("test-job-123")
        
        assert result is not None
        assert result["status"] == "completed"
    
    @patch('job_status_redis.redis.Redis')
    def test_get_job_not_found(self, mock_redis):
        """Test recupero job inesistente."""
        from job_status_redis import JobStatusRedis
        
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        
        manager = JobStatusRedis()
        manager._redis = mock_redis_instance
        manager._use_redis = True
        
        result = manager.get("nonexistent-job")
        
        assert result is None
    
    @patch('job_status_redis.redis.Redis')
    def test_update_job_status(self, mock_redis):
        """Test aggiornamento stato job."""
        from job_status_redis import JobStatusRedis
        
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = json.dumps({
            "status": "processing",
            "progress": 50
        })
        
        manager = JobStatusRedis()
        manager._redis = mock_redis_instance
        manager._use_redis = True
        
        manager.update("test-job", {"progress": 75})
        
        # Should call setex with updated data
        mock_redis_instance.setex.assert_called()
    
    def test_fallback_memory(self):
        """Test fallback in memoria quando Redis non disponibile."""
        from job_status_redis import JobStatusRedis
        
        manager = JobStatusRedis()
        manager._use_redis = False
        
        manager.set("fallback-job", {"status": "test"})
        result = manager.get("fallback-job")
        
        assert result is not None
        assert result["status"] == "test"
    
    @patch('job_status_redis.redis.Redis')
    def test_redis_connection_error(self, mock_redis):
        """Test gestione errore connessione Redis."""
        from job_status_redis import JobStatusRedis
        import redis
        
        mock_redis.side_effect = redis.ConnectionError("Connection refused")
        
        manager = JobStatusRedis()
        
        # Should fallback to memory
        assert manager._use_redis is False
        
        # Should still work with memory
        manager.set("test-job", {"status": "test"})
        result = manager.get("test-job")
        
        assert result is not None


class TestJobStatusKey:
    """Test per generazione chiavi."""
    
    def test_key_generation(self):
        """Test generazione chiave Redis."""
        from job_status_redis import JobStatusRedis
        
        manager = JobStatusRedis()
        key = manager._key("test-job-123")
        
        assert "musictext:job:" in key
        assert "test-job-123" in key
    
    def test_key_with_prefix(self):
        """Test chiave con prefix personalizzato."""
        from job_status_redis import JobStatusRedis
        
        with patch('job_status_redis.REDIS_KEY_PREFIX', 'custom:'):
            manager = JobStatusRedis()
            key = manager._key("job-1")
            
            assert "custom:" in key

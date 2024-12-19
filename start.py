import logging.config

from core.monitoring_service import MonitoringService

logging.config.fileConfig('core/config/logging_config.ini')
logger = logging.getLogger('ServiceLogger')

if __name__ == "__main__":
    logger.info("Starting application.")
    service = MonitoringService()
    service.start()

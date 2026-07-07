from django.apps import AppConfig


class MarketFinderConfig(AppConfig):
    name = 'market_finder'

    def ready(self):
        """Start the background scheduler when Django boots."""
        # Only start in the main process (not in reloader child)
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        try:
            from . import scheduler
            scheduler.start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Scheduler failed to start: {e}")
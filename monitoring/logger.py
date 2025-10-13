"""
Système de journalisation centralisé
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import colorlog


def setup_logger(name="trading_system", log_file=None):
    from config import settings

    """
    Configure et retourne un logger avec couleurs et fichier
    
    Args:
        name: Nom du logger
        log_file: Chemin du fichier de log (optionnel)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)

    # Éviter les doublons
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Format avec couleurs pour la console
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Handler fichier si activé
    if settings.LOG_TO_FILE:
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = settings.LOGS_DIR / f"trading_{timestamp}.log"

        file_formatter = logging.Formatter(settings.LOG_FORMAT)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

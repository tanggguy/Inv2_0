"""
Portfolio State Manager - Sauvegarde et restauration de l'état du portefeuille
"""

import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime
import threading
import time
from monitoring.logger import setup_logger

logger = setup_logger("portfolio_state")


class PortfolioStateManager:
    """
    Gestionnaire de l'état du portefeuille
    Sauvegarde périodique et restauration après crash
    """

    def __init__(self, config):
        """
        Initialise le gestionnaire

        Args:
            config: Configuration du paper trading
        """
        self.config = config["portfolio_state"]
        self.backup_dir = Path(self.config["backup_dir"])
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # État actuel
        self.current_state = {
            "timestamp": None,
            "account": {},
            "positions": {},
            "orders": {},
            "strategies": {},
            "performance": {},
            "circuit_breakers": {},
        }

        # Threading pour sauvegarde automatique
        self._save_thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        logger.info(f"PortfolioStateManager initialisé - Backup dir: {self.backup_dir}")

    def start(self):
        """Démarre la sauvegarde automatique"""
        if self.config["enabled"] and not self._save_thread:
            self._stop_event.clear()
            self._save_thread = threading.Thread(target=self._auto_save_loop)
            self._save_thread.daemon = True
            self._save_thread.start()
            logger.info("Sauvegarde automatique démarrée")

    def stop(self):
        """Arrête la sauvegarde automatique"""
        if self._save_thread:
            self._stop_event.set()
            self._save_thread.join(timeout=5)
            self._save_thread = None

            # Faire une dernière sauvegarde
            if self.config["save_on_shutdown"]:
                self.save_state()

            logger.info("Sauvegarde automatique arrêtée")

    def _auto_save_loop(self):
        """Boucle de sauvegarde automatique"""
        while not self._stop_event.is_set():
            try:
                # Attendre l'intervalle
                if self._stop_event.wait(self.config["save_interval_seconds"]):
                    break

                # Sauvegarder
                self.save_state()

            except Exception as e:
                logger.error(f"Erreur dans la boucle de sauvegarde: {e}")

    def update_state(self, component, data):
        """
        Met à jour une partie de l'état

        Args:
            component: Nom du composant ('account', 'positions', etc.)
            data: Données à sauvegarder
        """
        with self._lock:
            self.current_state[component] = data
            self.current_state["timestamp"] = datetime.now().isoformat()

            # Sauvegarde immédiate si configuré
            if component == "orders" and self.config.get("save_on_trade", False):
                self.save_state()

    def save_state(self):
        """Sauvegarde l'état actuel"""
        try:
            with self._lock:
                # Créer le nom de fichier
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"portfolio_state_{timestamp}.json"

                if self.config.get("compression", False):
                    filename += ".gz"
                    filepath = self.backup_dir / filename

                    # Sauvegarder avec compression
                    with gzip.open(filepath, "wt", encoding="utf-8") as f:
                        json.dump(self.current_state, f, indent=2, default=str)
                else:
                    filepath = self.backup_dir / filename

                    # Sauvegarder sans compression
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(self.current_state, f, indent=2, default=str)

                logger.info(f"État sauvegardé: {filepath}")

                # Créer un lien vers le dernier état
                latest_link = self.backup_dir / "latest_state.json"
                if latest_link.exists():
                    latest_link.unlink()

                # Copier le fichier actuel comme latest
                if self.config.get("compression", False):
                    # Décompresser pour le latest
                    with gzip.open(filepath, "rt") as f_in:
                        with open(latest_link, "w") as f_out:
                            f_out.write(f_in.read())
                else:
                    shutil.copy2(filepath, latest_link)

                # Rotation des backups
                if self.config.get("rotate_backups", True):
                    self._rotate_backups()

        except Exception as e:
            logger.error(f"Erreur sauvegarde état: {e}")

    def load_latest_state(self):
        """Charge le dernier état sauvegardé"""
        try:
            latest_file = self.backup_dir / "latest_state.json"

            if not latest_file.exists():
                # Chercher le fichier le plus récent
                backup_files = sorted(self.backup_dir.glob("portfolio_state_*.json*"))
                if not backup_files:
                    logger.warning("Aucun état sauvegardé trouvé")
                    return None
                latest_file = backup_files[-1]

            # Charger le fichier
            if str(latest_file).endswith(".gz"):
                with gzip.open(latest_file, "rt", encoding="utf-8") as f:
                    state = json.load(f)
            else:
                with open(latest_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

            with self._lock:
                self.current_state = state

            logger.info(f"État restauré depuis: {latest_file}")
            logger.info(f"Timestamp: {state.get('timestamp', 'Unknown')}")

            return state

        except Exception as e:
            logger.error(f"Erreur chargement état: {e}")
            return None

    def _rotate_backups(self):
        """Supprime les anciens backups"""
        try:
            max_backups = self.config.get("max_backups", 100)

            # Lister tous les backups
            backup_files = sorted(self.backup_dir.glob("portfolio_state_*.json*"))

            # Supprimer les plus anciens
            if len(backup_files) > max_backups:
                files_to_delete = backup_files[:-max_backups]
                for file in files_to_delete:
                    file.unlink()
                    logger.debug(f"Backup supprimé: {file}")

                logger.info(f"Rotation: {len(files_to_delete)} backups supprimés")

        except Exception as e:
            logger.error(f"Erreur rotation backups: {e}")

    def get_state_summary(self):
        """Retourne un résumé de l'état actuel"""
        with self._lock:
            summary = {
                "timestamp": self.current_state.get("timestamp"),
                "account_value": self.current_state.get("account", {}).get(
                    "portfolio_value"
                ),
                "cash": self.current_state.get("account", {}).get("cash"),
                "positions_count": len(self.current_state.get("positions", {})),
                "open_orders": len(self.current_state.get("orders", {})),
                "active_strategies": len(self.current_state.get("strategies", {})),
            }

            # Ajouter les positions
            positions = []
            for symbol, pos in self.current_state.get("positions", {}).items():
                positions.append(
                    {
                        "symbol": symbol,
                        "qty": pos.get("qty"),
                        "value": pos.get("market_value"),
                        "pnl": pos.get("unrealized_pl"),
                    }
                )
            summary["positions"] = positions

            return summary

    def export_history(self, start_date=None, end_date=None, output_file=None):
        """
        Exporte l'historique des états

        Args:
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            output_file: Fichier de sortie (optionnel)
        """
        try:
            # Collecter tous les fichiers de backup
            backup_files = sorted(self.backup_dir.glob("portfolio_state_*.json*"))

            history = []
            for filepath in backup_files:
                # Extraire la date du nom de fichier
                filename = filepath.stem
                if filename.endswith(".json"):
                    filename = filename[:-5]
                date_str = filename.replace("portfolio_state_", "")

                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")

                    # Filtrer par dates si spécifiées
                    if start_date and file_date < start_date:
                        continue
                    if end_date and file_date > end_date:
                        continue

                    # Charger le fichier
                    if str(filepath).endswith(".gz"):
                        with gzip.open(filepath, "rt", encoding="utf-8") as f:
                            state = json.load(f)
                    else:
                        with open(filepath, "r", encoding="utf-8") as f:
                            state = json.load(f)

                    history.append(
                        {
                            "date": file_date.isoformat(),
                            "file": filepath.name,
                            "state": state,
                        }
                    )

                except Exception as e:
                    logger.warning(f"Impossible de lire {filepath}: {e}")

            # Sauvegarder si demandé
            if output_file:
                output_path = Path(output_file)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(history, f, indent=2, default=str)
                logger.info(f"Historique exporté vers: {output_path}")

            return history

        except Exception as e:
            logger.error(f"Erreur export historique: {e}")
            return []

#!/usr/bin/env python3
"""
Script de lancement du dashboard Streamlit
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Lance le dashboard Streamlit"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           📊 TRADING SYSTEM DASHBOARD - STREAMLIT 📊                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Vérifier que Streamlit est installé
    try:
        import streamlit
        print(f"✅ Streamlit version {streamlit.__version__} détecté")
    except ImportError:
        print("❌ Streamlit n'est pas installé")
        print("\nInstallation de Streamlit...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
        print("✅ Streamlit installé avec succès")
    
    # Vérifier Plotly
    try:
        import plotly
        print(f"✅ Plotly version {plotly.__version__} détecté")
    except ImportError:
        print("❌ Plotly n'est pas installé")
        print("\nInstallation de Plotly...")
        subprocess.run([sys.executable, "-m", "pip", "install", "plotly"])
        print("✅ Plotly installé avec succès")
    
    print("\n" + "="*70)
    print("🚀 LANCEMENT DU DASHBOARD...")
    print("="*70)
    
    # Chemin vers le dashboard
    dashboard_path = Path(__file__).parent.parent / "optimization" / "dashboard" / "app.py"
    
    if not dashboard_path.exists():
        print(f"❌ Fichier dashboard introuvable: {dashboard_path}")
        return 1
    
    print(f"\n📂 Chemin: {dashboard_path}")
    print("\n💡 Le dashboard va s'ouvrir dans votre navigateur...")
    print("   URL: http://localhost:8501")
    print("\n⚡ Fonctionnalités disponibles:")
    print("   🚀 Run Optimization - Lancer des optimisations")
    print("   📋 View History - Consulter l'historique")
    print("   ⚖️ Compare Runs - Comparer plusieurs runs")
    print("   🔬 Analyze Strategy - Analyse détaillée")
    
    print("\n" + "="*70)
    print("🔴 Pour arrêter: Ctrl+C")
    print("="*70 + "\n")
    
    # Lancer Streamlit
    try:
        subprocess.run([
            sys.executable, 
            "-m", 
            "streamlit", 
            "run", 
            str(dashboard_path),
            "--theme.base", "dark",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n⚠️ Dashboard arrêté par l'utilisateur")
        return 0
    except Exception as e:
        print(f"\n❌ Erreur lors du lancement: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
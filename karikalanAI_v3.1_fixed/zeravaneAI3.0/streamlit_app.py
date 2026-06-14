"""
கரிகாலன் AI (Karikalan AI) — Entry Point
Run: streamlit run streamlit_app.py
"""
import os, sys, runpy
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeravaneai"))
sys.path.insert(0, os.getcwd())
runpy.run_path("frontend/app.py", run_name="__main__")

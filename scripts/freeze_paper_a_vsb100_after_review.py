"""Freeze ONLY an independently approved successor; then run its guarded runner.
No review template is filled and no pending decision is promoted here.
"""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from paper_a_vsb100_freeze_guard import validate_review,digest,source_paths
FOLDER=ROOT/'docs/paper_a_confirmation/successor_vsb100_20261117'
def main():
    protocol,recipe,rows,review,pins=validate_review(FOLDER)
    target=FOLDER/'FREEZE_RECEIPT.json'
    if target.exists():raise RuntimeError('Freeze receipt already exists; use guarded executor')
    reviewed=[(FOLDER/name).relative_to(ROOT).as_posix() for name in review['reviewed_files']]+[(FOLDER/'INDEPENDENT_REVIEW.json').relative_to(ROOT).as_posix()]
    paths=sorted(set(reviewed+source_paths()))
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    subprocess.run(['git','commit','--only','-m','freeze(paper-a): independently reviewed VSB100 three-domain successor','--',*paths],cwd=ROOT,check=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    with target.open('x',encoding='utf-8') as f:json.dump({'freeze_commit':commit,'review_sha256':digest(FOLDER/'INDEPENDENT_REVIEW.json'),'created_utc':datetime.now(timezone.utc).isoformat(),'confirmatory_GT_or_outcomes_opened':False},f,indent=2)
    print('Freeze committed before GT: '+commit)
if __name__=='__main__':main()

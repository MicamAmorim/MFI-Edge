"""Development-only next-model prototype. Not a validated adaptive detector.

Architecture follows the predeclared two map features and four fixed heads.
No test outcome may fit routing, normalization, head ordering or thresholds.
"""
from dataclasses import dataclass
import numpy as np

HEADS=('H1_equal_mean','H1_maximum','H2_equal_mean','H2_choquet_generalized_150')
FEATURES=('H1_map_mean_gap','H2_pairwise_map_correlation')
@dataclass(frozen=True)
class TrainingIdentity:
    image_id:str
    original_sha256:str
    scene_id:str
    split_role:str

class ConditionalRewardRouter:
    def __init__(self,*,blocked_original_hashes,blocked_scenes,alpha=1.0):
        if alpha!=1.0:raise ValueError('Prototype alpha fixed before new-model evaluation')
        self.blocked_hashes=frozenset(blocked_original_hashes);self.blocked_scenes=frozenset(blocked_scenes);self.alpha=alpha;self.fitted=False
    def fit(self,X,rewards,identities,*,confirmation_analysis_completed=False):
        if not confirmation_analysis_completed:raise PermissionError('Complete the preceding fixed confirmation analysis first')
        x=np.asarray(X,dtype=float);y=np.asarray(rewards,dtype=float);ids=list(identities)
        if x.ndim!=2 or x.shape[1]!=2 or len(x)<4 or y.shape!=(len(x),4) or len(ids)!=len(x):raise ValueError('Need >=4 unique development scenes, two fixed features and four head rewards')
        if not np.isfinite(x).all() or not np.isfinite(y).all() or (y<0).any() or (y>1).any():raise ValueError('Finite features and development F1 in[0,1] required')
        if any(r.split_role!='development_train' for r in ids):raise PermissionError('Only development_train labels may fit the router')
        if len({r.scene_id for r in ids})!=len(ids) or len({r.original_sha256 for r in ids})!=len(ids):raise ValueError('One training observation per original independent scene')
        if any(r.original_sha256 in self.blocked_hashes or r.scene_id in self.blocked_scenes for r in ids):raise PermissionError('Prior confirmation scenes are excluded from next-model fitting')
        self.mean=x.mean(0);self.scale=x.std(0);self.scale[self.scale==0]=1.;z=(x-self.mean)/self.scale;self.reward_mean=y.mean(0)
        self.coef=np.linalg.solve(z.T@z+self.alpha*np.eye(2),z.T@(y-self.reward_mean))
        self.best_fixed_index=int(np.argmax(self.reward_mean));self.training_ids=ids;self.fitted=True;return self
    def predicted_rewards(self,X):
        if not self.fitted:raise RuntimeError('Router has no fitted development model')
        x=np.asarray(X,dtype=float)
        if x.ndim!=2 or x.shape[1]!=2 or not np.isfinite(x).all():raise ValueError('Two finite GT-free features required')
        # A ranking surrogate, not a calibrated probability or guaranteed F1.
        return ((x-self.mean)/self.scale)@self.coef+self.reward_mean
    def select(self,X):return np.asarray(HEADS)[np.argmax(self.predicted_rewards(X),axis=1)]
    def artifact(self):
        if not self.fitted:raise RuntimeError('No fitted model to export')
        return {'schema':'MFI_Edge_next_conditional_router_development_v0','status':'DEVELOPMENT_ONLY_NOT_EXTERNALLY_VALIDATED','heads':list(HEADS),'features':list(FEATURES),'alpha':self.alpha,'mean':self.mean.tolist(),'scale':self.scale.tolist(),'reward_mean':self.reward_mean.tolist(),'coef':self.coef.tolist(),'best_fixed_head':HEADS[self.best_fixed_index],'training':[r.__dict__ for r in self.training_ids]}

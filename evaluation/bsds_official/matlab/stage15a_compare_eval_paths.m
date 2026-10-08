function stage15a_compare_eval_paths(pdollarDir, benchmarkDir, imageDir, gtDir, outDir)
% Compare Piotr Dollar's BSDS-compatible image evaluator with the pinned path.
%
% This is a fixture-only Stage-15a diagnostic. It does not edit vendored code
% or evaluate any BSDS train/validation/test detector predictions.

addpath(pdollarDir, '-begin');
addpath(benchmarkDir, '-end');

if ~exist(outDir, 'dir')
    mkdir(outDir);
end

imgs = dir(fullfile(imageDir, '*.jpg'));
if numel(imgs) ~= 5
    error('MFIEdge:FixtureSize', 'Expected five fixture images, found %d.', numel(imgs));
end

for i = 1:numel(imgs)
    [~, iid, ~] = fileparts(imgs(i).name);
    inFile = fullfile(imageDir, imgs(i).name);
    gtFile = fullfile(gtDir, [iid '.mat']);
    prFile = fullfile(outDir, [iid '_ev1.txt']);
    edgesEvalImg(inFile, gtFile, 'out', prFile, 'thrs', 5, ...
        'maxDist', 0.0075, 'thin', 1);
end

collect_eval_bdry(outDir);
end

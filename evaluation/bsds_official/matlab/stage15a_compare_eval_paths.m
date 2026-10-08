function stage15a_compare_eval_paths(pdollarDir, benchmarkDir, predictionDir, gtDir, outDir)
% Compare Piotr Dollar's BSDS-compatible image evaluator with the pinned path.
%
% This is a fixture-only Stage-15a diagnostic. It does not edit vendored code
% or evaluate any BSDS train/validation/test detector predictions.

addpath(pdollarDir, '-begin');
addpath(benchmarkDir, '-end');

if ~exist(outDir, 'dir')
    mkdir(outDir);
end

predictions = dir(fullfile(predictionDir, '*.png'));
if numel(predictions) ~= 5
    error('MFIEdge:FixtureSize', 'Expected five fixture predictions, found %d.', numel(predictions));
end

for i = 1:numel(predictions)
    [~, iid, ~] = fileparts(predictions(i).name);
    inFile = fullfile(predictionDir, predictions(i).name);
    gtFile = fullfile(gtDir, [iid '.mat']);
    prFile = fullfile(outDir, [iid '_ev1.txt']);
    edgesEvalImg(inFile, gtFile, 'out', prFile, 'thrs', 5, ...
        'maxDist', 0.0075, 'thin', 1);
end

collect_eval_bdry(outDir);
end

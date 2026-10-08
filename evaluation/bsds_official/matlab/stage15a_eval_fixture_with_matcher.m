function stage15a_eval_fixture_with_matcher(matcherDir, benchmarkDir, predictionDir, gtDir, outDir)
% Evaluate only the shipped five-image fixture with an explicit matcher build.

addpath(matcherDir, '-begin');
addpath(benchmarkDir, '-end');
resolved = which('correspondPixels');
if ~startsWith(lower(resolved), lower(matcherDir))
    error('MFIEdge:MatcherResolution', ...
        'Expected matcher under %s, resolved %s.', matcherDir, resolved);
end
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

predictions = dir(fullfile(predictionDir, '*.png'));
if numel(predictions) ~= 5
    error('MFIEdge:FixtureSize', 'Expected five fixture predictions, found %d.', numel(predictions));
end
for i = 1:numel(predictions)
    [~, iid, ~] = fileparts(predictions(i).name);
    evaluation_bdry_image(fullfile(predictionDir, predictions(i).name), ...
        fullfile(gtDir, [iid '.mat']), fullfile(outDir, [iid '_ev1.txt']), ...
        5, 0.0075, 1);
end
collect_eval_bdry(outDir);
end

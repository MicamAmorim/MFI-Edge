function stage15a_eval_fixture_with_matcher(matcherDir, benchmarkDir, predictionDir, gtDir, outDir)
% Evaluate only the shipped five-image fixture with an explicit matcher build.

addpath(matcherDir, '-begin');
addpath(benchmarkDir, '-end');

% Apply the audited syntax-only compatibility transform used by the main
% repository evaluator. MATLAB R2023a cannot parse the pinned source's
% groundTruth{i}.Boundaries expression, and its fourth fileparts output is no
% longer supported. The vendored source remains byte-unchanged.
compatDir = fullfile(outDir, 'matlab_compat');
if ~exist(compatDir, 'dir')
    mkdir(compatDir);
end
sourceEval = fullfile(benchmarkDir, 'evaluation_bdry_image.m');
compatEval = fullfile(compatDir, 'evaluation_bdry_image.m');
compatSource = fileread(sourceEval);
oldLoop = 'for i = 1:numel(groundTruth),';
newLoop = sprintf('for i = 1:numel(groundTruth),\n        gt_i = groundTruth{i};');
oldAccess = 'groundTruth{i}.Boundaries';
oldFileparts = '[p,n,e,v]=fileparts(inFile);';
oldLoad = 'load(gtFile);';
newLoad = sprintf('gtData = load(gtFile);\ngroundTruth = gtData.groundTruth;');
if ~contains(compatSource, oldLoop) || ~contains(compatSource, oldAccess) || ...
        ~contains(compatSource, oldFileparts) || ~contains(compatSource, oldLoad)
    error('MFIEdge:UnexpectedEvaluatorSource', ...
        'Pinned evaluation_bdry_image.m no longer matches the audited compatibility transform.');
end
compatSource = strrep(compatSource, oldLoop, newLoop);
compatSource = strrep(compatSource, oldAccess, 'gt_i.Boundaries');
compatSource = strrep(compatSource, oldFileparts, '[p,n,e]=fileparts(inFile);');
compatSource = strrep(compatSource, oldLoad, newLoad);
fid = fopen(compatEval, 'w');
if fid == -1
    error('MFIEdge:WriteFailed', 'Could not write MATLAB compatibility mirror: %s', compatEval);
end
fprintf(fid, '%s', compatSource);
fclose(fid);
addpath(compatDir, '-begin');

resolved = which('correspondPixels');
resolvedNorm = strrep(lower(resolved), '\', '/');
matcherNorm = strip(strrep(lower(matcherDir), '\', '/'), 'right', '/');
if ~(strcmp(resolvedNorm, matcherNorm) || startsWith(resolvedNorm, [matcherNorm '/']))
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

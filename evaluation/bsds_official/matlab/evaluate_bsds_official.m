function evaluate_bsds_official(benchmarkDir, imageDir, gtDir, pbDir, outDir, nthresh, maxDist, thinpb, phase)
% MFI-Edge thin wrapper around the original Berkeley BSDS boundary evaluator.
%
% It intentionally delegates matching and aggregation to the original
% evaluation_bdry_image.m / collect_eval_bdry.m implementation. The wrapper is
% Windows-safe (it does not call boundaryBench.m's Unix `rm`) and writes a JSON
% summary for the Python research controller.

if nargin < 8, thinpb = 1; end
if nargin < 7, maxDist = 0.0075; end
if nargin < 6, nthresh = 99; end
if nargin < 9, phase = 'all'; end
if ~ismember(phase, {'all', 'evaluate', 'collect'})
    error('MFIEdge:InvalidPhase', 'Unknown evaluator phase: %s', phase);
end

% MATLAB R2023a cannot parse the pinned evaluator's chained expression
% ``groundTruth{i}.Boundaries``.  Do not edit the vendored checkout: create a
% run-local syntax-compatible mirror whose only changes make the dynamically
% loaded ground-truth variable explicit and assign its cell element to ``gt_i``
% before field access.  The matching/counting algorithm is otherwise inherited
% byte-for-byte from the pinned source.
addpath(benchmarkDir, '-end');

if ~exist(outDir, 'dir')
    mkdir(outDir);
end

imgs = dir(fullfile(imageDir, '*.jpg'));
if isempty(imgs)
    error('MFIEdge:NoImages', 'No JPG images found in %s', imageDir);
end

if ~strcmp(phase, 'collect')
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
    % The pinned source asks fileparts for a fourth output that modern MATLAB
    % does not provide. That legacy value is never used by the evaluator.
    compatSource = strrep(compatSource, oldFileparts, '[p,n,e]=fileparts(inFile);');
    compatSource = strrep(compatSource, oldLoad, newLoad);
    fid = fopen(compatEval, 'w');
    if fid == -1
        error('MFIEdge:WriteFailed', 'Could not write MATLAB compatibility mirror: %s', compatEval);
    end
    fprintf(fid, '%s', compatSource);
    fclose(fid);

    % Keep the run-local compatibility function ahead of the pinned benchmark
    % directory while leaving all other Berkeley functions/MEX files unchanged.
    addpath(compatDir, '-begin');

    mexFile = fullfile(benchmarkDir, ['correspondPixels.' mexext]);
    % MATLAB reports compiled MEX binaries as file type 3, while ordinary
    % source/data files are type 2. Accept either kind of existing file.
    if ~ismember(exist(mexFile, 'file'), [2 3])
        error('MFIEdge:MissingMEX', 'Missing correspondPixels MEX for this platform: %s', mexFile);
    end
    if exist('bwmorph', 'file') == 0
        error('MFIEdge:MissingToolbox', 'bwmorph is unavailable; MATLAB Image Processing Toolbox is required.');
    end

    for i = 1:numel(imgs)
        [~, iid, ~] = fileparts(imgs(i).name);
        inFile = fullfile(pbDir, [iid '.png']);
        if ~exist(inFile, 'file')
            inFile = fullfile(pbDir, [iid '.mat']);
        end
        if ~exist(inFile, 'file')
            error('MFIEdge:MissingPrediction', 'Missing prediction for image %s', iid);
        end

        gtFile = fullfile(gtDir, [iid '.mat']);
        if ~exist(gtFile, 'file')
            error('MFIEdge:MissingGT', 'Missing BSDS ground truth for image %s', iid);
        end

        evFile = fullfile(outDir, [iid '_ev1.txt']);
        evaluation_bdry_image(inFile, gtFile, evFile, nthresh, maxDist, logical(thinpb));
        fprintf('MFI_BSDS_EVAL %d/%d %s\n', i, numel(imgs), iid);
    end
end

if strcmp(phase, 'evaluate')
    return;
end

[bestF, bestP, bestR, bestT, Fmax, Pmax, Rmax, areaPR] = collect_eval_bdry(outDir);

summary = struct();
summary.ODS = bestF;
summary.ODS_precision = bestP;
summary.ODS_recall = bestR;
summary.ODS_threshold = bestT;
summary.OIS = Fmax;
summary.OIS_precision = Pmax;
summary.OIS_recall = Rmax;
summary.AP = areaPR;
summary.n_images = numel(imgs);
summary.nthresh = nthresh;
summary.max_dist = maxDist;
summary.thinpb = logical(thinpb);
summary.matcher = 'Berkeley correspondPixels / CSA++';
summary.annotation_protocol = 'all human boundary annotations, original Berkeley accumulation';
summary.matlab_compatibility = 'run-local syntax-only explicit groundTruth load/cell assignment and unused fourth fileparts output removal; native matching and aggregation may run in isolated MATLAB processes; pinned vendor source unchanged';

fid = fopen(fullfile(outDir, 'official_summary.json'), 'w');
if fid == -1
    error('MFIEdge:WriteFailed', 'Could not write official_summary.json');
end
fprintf(fid, '%s', jsonencode(summary));
fclose(fid);
end

function evaluate_bsds_official(benchmarkDir, imageDir, gtDir, pbDir, outDir, nthresh, maxDist, thinpb)
% MFI-Edge thin wrapper around the original Berkeley BSDS boundary evaluator.
%
% It intentionally delegates matching and aggregation to the original
% evaluation_bdry_image.m / collect_eval_bdry.m implementation. The wrapper is
% Windows-safe (it does not call boundaryBench.m's Unix `rm`) and writes a JSON
% summary for the Python research controller.

if nargin < 8, thinpb = 1; end
if nargin < 7, maxDist = 0.0075; end
if nargin < 6, nthresh = 99; end

addpath(benchmarkDir);

mexFile = fullfile(benchmarkDir, ['correspondPixels.' mexext]);
if exist(mexFile, 'file') ~= 2
    error('MFIEdge:MissingMEX', 'Missing correspondPixels MEX for this platform: %s', mexFile);
end
if exist('bwmorph', 'file') == 0
    error('MFIEdge:MissingToolbox', 'bwmorph is unavailable; MATLAB Image Processing Toolbox is required.');
end

if ~exist(outDir, 'dir')
    mkdir(outDir);
end

imgs = dir(fullfile(imageDir, '*.jpg'));
if isempty(imgs)
    error('MFIEdge:NoImages', 'No JPG images found in %s', imageDir);
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

fid = fopen(fullfile(outDir, 'official_summary.json'), 'w');
if fid == -1
    error('MFIEdge:WriteFailed', 'Could not write official_summary.json');
end
fprintf(fid, '%s', jsonencode(summary));
fclose(fid);
end

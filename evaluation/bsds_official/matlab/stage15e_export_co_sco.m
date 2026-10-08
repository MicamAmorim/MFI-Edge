function stage15e_export_co_sco(coSourceDir, scoSourceDir, imageDir, ...
        coOutputDir, scoOutputDir, runtimeCsv)
% Batch adapter for the unmodified author CO and SCO MATLAB implementations.
%
% The detector sources remain byte-identical to the pinned institutional
% archives. This adapter supplies deterministic I/O, fixed published
% parameters, validation, timing, and 8-bit serialization only.

if ~exist(coOutputDir, 'dir'), mkdir(coOutputDir); end
if ~exist(scoOutputDir, 'dir'), mkdir(scoOutputDir); end
files = dir(fullfile(imageDir, '*.jpg'));
[~, order] = sort({files.name});
files = files(order);
if isempty(files)
    error('Stage15e:NoImages', 'No JPG images found in %s', imageDir);
end

fid = fopen(runtimeCsv, 'w');
if fid < 0
    error('Stage15e:RuntimeCSV', 'Could not create %s', runtimeCsv);
end
cleanupObj = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, 'method,image_id,seconds,min_score,max_score\n');

% The 2015 paper fixes sigma=1.1 and w=-0.7 after BSDS300-train
% optimization. Eight orientations are embedded in both released demos.
addpath(coSourceDir, '-begin');
rehash;
assert_source('COBoundary', fullfile(coSourceDir, 'COBoundary.m'));
for index = 1:numel(files)
    [~, imageId, ~] = fileparts(files(index).name);
    fprintf('STAGE15E_CO_EXPORT %03d/%03d %s\n', index, numel(files), imageId);
    input = im2double(imread(fullfile(imageDir, files(index).name)));
    started = tic;
    score = COBoundary(input, 1.1, 8, -0.7);
    seconds = toc(started);
    validate_and_write(score, input, coOutputDir, imageId, 'CO');
    fprintf(fid, 'co,%s,%.9f,%.17g,%.17g\n', imageId, seconds, ...
        min(score(:)), max(score(:)));
end
rmpath(coSourceDir);
clear COBoundary resDO OrientedDoubleOpponent SingleOpponent DivGauss2D ...
    gaus conByfft nonmax;

% The author SCO release fixes sigma=1.1, w=-0.7, eight orientations,
% and the spatial-sparseness window eta=5.
addpath(scoSourceDir, '-begin');
rehash;
assert_source('SCOBoundary', fullfile(scoSourceDir, 'SCOBoundary.m'));
for index = 1:numel(files)
    [~, imageId, ~] = fileparts(files(index).name);
    fprintf('STAGE15E_SCO_EXPORT %03d/%03d %s\n', index, numel(files), imageId);
    input = im2double(imread(fullfile(imageDir, files(index).name)));
    started = tic;
    score = SCOBoundary(input, 1.1, 8, -0.7, 5);
    seconds = toc(started);
    validate_and_write(score, input, scoOutputDir, imageId, 'SCO');
    fprintf(fid, 'sco,%s,%.9f,%.17g,%.17g\n', imageId, seconds, ...
        min(score(:)), max(score(:)));
end
end

function assert_source(functionName, expected)
resolved = which(functionName);
if isempty(resolved) || ~strcmpi(char(java.io.File(resolved).getCanonicalPath()), ...
        char(java.io.File(expected).getCanonicalPath()))
    error('Stage15e:WrongSource', '%s did not resolve to the pinned archive.', ...
        functionName);
end
end

function validate_and_write(score, input, outputDir, imageId, method)
score = double(score);
if ndims(score) ~= 2 || size(score, 1) ~= size(input, 1) || ...
        size(score, 2) ~= size(input, 2)
    error('Stage15e:MapShape', 'Unexpected %s map shape for %s', method, imageId);
end
if any(~isfinite(score(:)))
    error('Stage15e:NonFinite', 'Non-finite %s response for %s', method, imageId);
end
minScore = min(score(:));
maxScore = max(score(:));
if minScore < -1e-9 || maxScore > 1 + 1e-9
    error('Stage15e:MapRange', '%s response outside [0,1] for %s: [%g,%g]', ...
        method, imageId, minScore, maxScore);
end
% Both author detectors perform intrinsic per-image normalization and NMS.
% This is only the fixed benchmark serialization, with no adapter rescaling.
quantized = uint8(round(255 * min(max(score, 0), 1)));
imwrite(quantized, fullfile(outputDir, [imageId '.png']));
end

function stage16b_export_sed_png(authorSourceDir, imageDir, outputDir, runtimeCsv)
% Dataset-agnostic PNG batch adapter for the unchanged author SED detector.
%
% Stage 16b uses this only for the resized UDED-selection inputs. BSDS500
% validation reuses the already frozen exact Stage-15b maps when available.

addpath(authorSourceDir, '-begin');
rehash;
resolved = which('SurroundModulationEdgeDetector');
expected = fullfile(authorSourceDir, 'SurroundModulationEdgeDetector.m');
if isempty(resolved) || ~strcmpi(char(java.io.File(resolved).getCanonicalPath()), ...
        char(java.io.File(expected).getCanonicalPath()))
    error('Stage16b:WrongSEDSource', ...
        'SurroundModulationEdgeDetector did not resolve to the pinned author checkout.');
end

if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end
files = dir(fullfile(imageDir, '*.png'));
[~, order] = sort({files.name});
files = files(order);
if isempty(files)
    error('Stage16b:NoImages', 'No PNG images found in %s', imageDir);
end

fid = fopen(runtimeCsv, 'w');
if fid < 0
    error('Stage16b:RuntimeCSV', 'Could not create %s', runtimeCsv);
end
cleanupObj = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, 'image_id,seconds,min_score,max_score\n');

for index = 1:numel(files)
    [~, imageId, ~] = fileparts(files(index).name);
    fprintf('STAGE16B_SED_EXPORT %03d/%03d %s\n', index, numel(files), imageId);
    input = imread(fullfile(imageDir, files(index).name));
    started = tic;
    score = SurroundModulationEdgeDetector(input);
    seconds = toc(started);
    score = double(score);
    if ndims(score) ~= 2 || size(score, 1) ~= size(input, 1) || ...
            size(score, 2) ~= size(input, 2)
        error('Stage16b:MapShape', 'Unexpected SED map shape for %s', imageId);
    end
    if any(~isfinite(score(:)))
        error('Stage16b:NonFinite', 'Non-finite SED response for %s', imageId);
    end
    minScore = min(score(:));
    maxScore = max(score(:));
    if minScore < -1e-9 || maxScore > 1 + 1e-9
        error('Stage16b:MapRange', ...
            'SED response outside [0,1] for %s: [%g,%g]', ...
            imageId, minScore, maxScore);
    end
    quantized = uint8(round(255 * min(max(score, 0), 1)));
    imwrite(quantized, fullfile(outputDir, [imageId '.png']));
    fprintf(fid, '%s,%.9f,%.17g,%.17g\n', ...
        imageId, seconds, minScore, maxScore);
end
end

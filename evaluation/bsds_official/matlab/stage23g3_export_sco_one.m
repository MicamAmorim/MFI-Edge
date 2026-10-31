function stage23g3_export_sco_one(sourceDir, inputPath, outputPath)
% Execute one atomic exact-author SCO unit for Stage 23G3.

addpath(sourceDir, '-begin');
rehash;
expected = fullfile(sourceDir, 'SCOBoundary.m');
resolved = which('SCOBoundary');
if isempty(resolved) || ~strcmpi(char(java.io.File(resolved).getCanonicalPath()), ...
        char(java.io.File(expected).getCanonicalPath()))
    error('Stage23G3:WrongSource', 'SCOBoundary did not resolve to pinned source.');
end

input = im2double(imread(inputPath));
if ndims(input) ~= 3 || size(input, 3) ~= 3
    error('Stage23G3:InputShape', 'Expected one RGB raster.');
end
started = tic;
score = double(SCOBoundary(input, 1.1, 8, -0.7, 5));
seconds = toc(started);
if ndims(score) ~= 2 || size(score, 1) ~= size(input, 1) || ...
        size(score, 2) ~= size(input, 2)
    error('Stage23G3:MapShape', 'Unexpected SCO output shape.');
end
if any(~isfinite(score(:)))
    error('Stage23G3:NonFinite', 'SCO output contains non-finite values.');
end
lo = min(score(:)); hi = max(score(:));
if lo < -1e-9 || hi > 1 + 1e-9
    error('Stage23G3:MapRange', 'SCO response outside [0,1]: [%g,%g].', lo, hi);
end

[parent, stem, ext] = fileparts(outputPath);
if ~exist(parent, 'dir'), mkdir(parent); end
temporary = fullfile(parent, [stem '.tmp' ext]);
imwrite(uint8(round(255 * min(max(score, 0), 1))), temporary);
movefile(temporary, outputPath, 'f');
fprintf('STAGE23G3_SCO_OK seconds=%.9f min=%.17g max=%.17g\n', ...
    seconds, lo, hi);
end

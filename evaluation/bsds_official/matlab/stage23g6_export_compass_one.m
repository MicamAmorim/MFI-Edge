function stage23g6_export_compass_one(source_dir, build_dir, input_path, output_path)
% Atomic one-image adapter for unchanged Ruzon/Tomasi Compass author code.

if ~exist(build_dir, 'dir'), mkdir(build_dir); end
mex_path = fullfile(build_dir, ['compassmex.' mexext]);
if ~exist(mex_path, 'file')
    mex('-compatibleArrayDims', '-outdir', build_dir, '-output', 'compassmex', ...
        fullfile(source_dir, 'compassmex.c'), fullfile(source_dir, 'compass.c'), ...
        fullfile(source_dir, 'bs.c'), fullfile(source_dir, 'RGBLab.c'), ...
        fullfile(source_dir, 'emd.c'));
end
addpath(build_dir);

image = imread(input_path);
started = tic;
strength = compassmex(image, 4, 1, 1, 180, 6, 10);
elapsed = toc(started);
radius = 12;
expected = [size(image,1) - 2 * radius + 1, size(image,2) - 2 * radius + 1];
if ndims(strength) ~= 2 || ~isequal(size(strength), expected) || ...
        any(~isfinite(strength(:))) || min(strength(:)) < 0 || max(strength(:)) > 1
    error('Invalid Compass response for %s', input_path);
end
native = zeros(size(image,1), size(image,2));
native(radius + 1:size(image,1) - radius + 1, ...
       radius + 1:size(image,2) - radius + 1) = strength;
temporary = [output_path '.tmp.png'];
if exist(temporary, 'file'), delete(temporary); end
imwrite(uint8(round(255 * native)), temporary);
movefile(temporary, output_path, 'f');
fprintf('STAGE23G6_COMPASS_OK seconds=%.17g min=%.17g max=%.17g\n', ...
    elapsed, min(strength(:)), max(strength(:)));
end

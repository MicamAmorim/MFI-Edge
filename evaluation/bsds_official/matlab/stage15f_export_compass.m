function stage15f_export_compass(source_dir, build_dir, image_dir, output_dir, runtime_csv)
% Batch adapter for the unchanged Ruzon/Tomasi Compass MEX implementation.
% The detector sees images only; the adapter restores author-valid centers to
% native image coordinates and serializes the fixed maximum-EMD strength.

if ~exist(build_dir, 'dir'), mkdir(build_dir); end
if ~exist(output_dir, 'dir'), mkdir(output_dir); end
mex('-compatibleArrayDims', '-outdir', build_dir, '-output', 'compassmex', ...
    fullfile(source_dir, 'compassmex.c'), fullfile(source_dir, 'compass.c'), ...
    fullfile(source_dir, 'bs.c'), fullfile(source_dir, 'RGBLab.c'), ...
    fullfile(source_dir, 'emd.c'));
addpath(build_dir);

files = dir(fullfile(image_dir, '*.jpg'));
[~, order] = sort({files.name}); files = files(order);
fid = fopen(runtime_csv, 'w');
if fid < 0, error('Could not open runtime CSV: %s', runtime_csv); end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'image_id,seconds\n');
radius = 12;
for k = 1:numel(files)
    image_id = erase(files(k).name, '.jpg');
    image = imread(fullfile(image_dir, files(k).name));
    started = tic;
    strength = compassmex(image, 4, 1, 1, 180, 6, 10);
    elapsed = toc(started);
    if ndims(strength) ~= 2 || any(~isfinite(strength(:))) || ...
            min(strength(:)) < 0 || max(strength(:)) > 1
        error('Invalid Compass response for %s', image_id);
    end
    expected = [size(image,1) - 2 * radius + 1, size(image,2) - 2 * radius + 1];
    if ~isequal(size(strength), expected)
        error('Unexpected Compass response size for %s', image_id);
    end
    native = zeros(size(image,1), size(image,2));
    native(radius + 1:size(image,1) - radius + 1, ...
           radius + 1:size(image,2) - radius + 1) = strength;
    imwrite(uint8(round(255 * native)), fullfile(output_dir, [image_id '.png']));
    fprintf(fid, '%s,%.17g\n', image_id, elapsed);
end
fprintf('STAGE15F_COMPASS_EXPORT_OK images=%d\n', numel(files));
end

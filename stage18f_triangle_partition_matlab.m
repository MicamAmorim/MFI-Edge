function stage18f_triangle_partition_matlab(authorRoot, inputDir, outputDir)
% Batch-only adapter around the immutable author triangle-partition detector.

addpath(authorRoot);
previousFolder = cd(authorRoot);
restoreFolder = onCleanup(@() cd(previousFolder)); %#ok<NASGU>
if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end
files = dir(fullfile(inputDir, '*.mat'));
[~, order] = sort({files.name});
files = files(order);
for index = 1:numel(files)
    payload = load(fullfile(inputDir, files(index).name), 'input_image');
    input_image = double(payload.input_image);
    assert(isequal(size(input_image), [129 129]));
    started = tic;
    [response, ~] = runIm(input_image, false, 0);
    author_runtime_seconds = toc(started);
    response = double(response);
    % The untouched author normalizer returns NaN on a zero-response flat
    % field.  The registered I/O adapter maps only non-finite values to zero.
    response(~isfinite(response)) = 0;
    response = min(max(response, 0), 1);
    save(fullfile(outputDir, files(index).name), ...
        'response', 'author_runtime_seconds', '-v7');
    fprintf('STAGE18F_AUTHOR_MAP %03d/%03d %s\n', ...
        index, numel(files), files(index).name);
end
fprintf('STAGE18F_AUTHOR_BATCH_OK maps=%d\n', numel(files));
end

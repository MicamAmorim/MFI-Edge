function export_stage16v_structured_forest(toolboxDir, edgesDir, modelPath, inputDir, outputDir)
% Exact pinned Dollár-Zitnick Structured Edge inference for Stage 16v.

addpath(genpath(toolboxDir));
addpath(edgesDir);
if ~exist(outputDir, 'dir'), mkdir(outputDir); end

loaded = load(modelPath);
model = loaded.model;
% edgesEval.m in the author toolbox enables detector NMS before evaluation.
model.opts.nms = 1;
% Runtime-only determinism; this does not alter the learned forest.
model.opts.nThreads = 1;

synthetic = zeros(64, 64, 3, 'uint8');
synthetic(:, 33:end, :) = 255;
repeatA = edgesDetect(synthetic, model);
repeatB = edgesDetect(synthetic, model);
assert(isequal(repeatA, repeatB));
assert(all(isfinite(repeatA(:))) && min(repeatA(:)) >= 0 && max(repeatA(:)) <= 1);

files = [dir(fullfile(inputDir, '*.jpg')); dir(fullfile(inputDir, '*.png'))];
[~, order] = sort({files.name});
files = files(order);
if isempty(files), error('No input JPG or PNG files found.'); end

runtimePath = fullfile(outputDir, 'per_image_runtime.csv');
fid = fopen(runtimePath, 'w');
assert(fid >= 0);
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'image_id,runtime_seconds,min_score,max_score\n');
rawMax = -inf;
rawAboveOne = 0;

for index = 1:numel(files)
    [~, imageId, ~] = fileparts(files(index).name);
    fprintf('STAGE16V_STRUCTURED_FOREST %03d/%03d %s\n', index, numel(files), imageId);
    image = imread(fullfile(inputDir, files(index).name));
    if size(image, 3) == 1, image = repmat(image, [1 1 3]); end
    started = tic;
    score = edgesDetect(image, model);
    elapsed = toc(started);
    % Match the author edgesEval.m serialization exactly. The learned/NMS
    % response can overshoot one slightly; uint8(E*255) saturates those values.
    assert(all(isfinite(score(:))) && min(score(:)) >= 0);
    rawMax = max(rawMax, double(max(score(:))));
    rawAboveOne = rawAboveOne + nnz(score(:) > 1);
    imwrite(uint8(255 * score), fullfile(outputDir, [imageId '.png']));
    fprintf(fid, '%s,%.9f,%.9f,%.9f\n', imageId, elapsed, min(score(:)), max(score(:)));
end

metadata = struct();
metadata.method = 'dollar_zitnick_structured_forest_modelBsds';
metadata.edges_commit = '94260b5d0fc068202598312e01a37604972dcc9e';
metadata.toolbox_commit = 'e87332637bbe8e8b92dd487c87567d9628404523';
metadata.model_file = 'models/forest/modelBsds.mat';
metadata.training_class = 'non-neural supervised structured random forest';
metadata.training_split = 'BSDS500 train, as fixed by author edgesTrain.m and model defaults';
metadata.nms = true;
metadata.nThreads = 1;
metadata.nTrees = double(model.opts.nTrees);
metadata.nTreesEval = double(model.opts.nTreesEval);
metadata.stride = double(model.opts.stride);
metadata.multiscale = logical(model.opts.multiscale);
metadata.sharpen = double(model.opts.sharpen);
metadata.seed = double(model.opts.seed);
metadata.active_nodes = double(nnz(model.count));
metadata.internal_threshold_nodes = double(nnz(model.child));
metadata.synthetic_repeat_bitwise_equal = true;
metadata.raw_max_score = rawMax;
metadata.raw_samples_above_one = double(rawAboveOne);
metadata.output = 'author score after author NMS, serialized exactly as uint8(E*255); uint8 conversion saturates rare raw overshoots';
metaFid = fopen(fullfile(outputDir, 'structured_forest_provenance.json'), 'w');
assert(metaFid >= 0);
fprintf(metaFid, '%s', jsonencode(metadata, PrettyPrint=true));
fclose(metaFid);
end

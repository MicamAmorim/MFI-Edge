function stage21b_estrada_jepson_eval(specFile, runtimeDir, kittDir, gtDir, outFile)
% Frozen-map Stage-21B Estrada--Jepson comparison using certified KITT code.
addpath(runtimeDir, '-begin');
addpath(kittDir, '-end');
spec = jsondecode(fileread(specFile));
thresholds = (1:99) ./ 100;
rows = struct([]);
params.maxDist = 0.025;
partialFile = [outFile '.partial.json'];
if isfile(partialFile)
    rows = jsondecode(fileread(partialFile));
end

for m = 1:numel(spec.methods)
    method = spec.methods(m);
    files = dir(fullfile(method.pred_dir, '*.png'));
    [~, order] = sort({files.name}); files = files(order);
    for ti = 1:numel(thresholds)
        t = thresholds(ti);
        if ~isempty(rows) && any(strcmp({rows.method}, method.name) & ...
                abs([rows.threshold] - t) < 1e-12)
            continue;
        end
        mp = 0; pp = 0; mr = 0; rr = 0;
        for i = 1:numel(files)
            [~, iid, ~] = fileparts(files(i).name);
            candidate = double(imread(fullfile(files(i).folder, files(i).name))) ./ 255 > t;
            data = load(fullfile(gtDir, [iid '.mat']));
            matched = false(size(candidate));
            for a = 1:numel(data.groundTruth)
                gt = logical(data.groundTruth{a}.Boundaries);
                match1 = estradaJepsonMatching(candidate, gt, params);
                match2 = estradaJepsonMatching(gt, candidate, params);
                matched = matched | logical(match1);
                mr = mr + sum(match2(:) > 0);
                rr = rr + sum(gt(:));
            end
            mp = mp + sum(matched(:));
            pp = pp + sum(candidate(:));
        end
        p = mp / (pp + (pp == 0));
        r = mr / (rr + (rr == 0));
        f = (p*r) / (0.5*p + 0.5*r + ((p+r) == 0));
        row = struct('method', method.name, 'threshold', t, ...
            'precision', p, 'recall', r, 'f_measure', f, ...
            'matched_prediction', mp, 'prediction_total', pp, ...
            'matched_recall', mr, 'recall_total', rr);
        if isempty(rows), rows = row; else, rows(end+1) = row; end %#ok<AGROW>
        checkpointFile = [partialFile '.tmp'];
        checkpoint = fopen(checkpointFile, 'w');
        if checkpoint == -1, error('MFIEdge:WriteFailed', 'Cannot write %s', checkpointFile); end
        fprintf(checkpoint, '%s', jsonencode(rows)); fclose(checkpoint);
        movefile(checkpointFile, partialFile, 'f');
    end
end
fid = fopen(outFile, 'w');
if fid == -1, error('MFIEdge:WriteFailed', 'Cannot write %s', outFile); end
fprintf(fid, '%s', jsonencode(rows)); fclose(fid);
if isfile(partialFile), delete(partialFile); end
end

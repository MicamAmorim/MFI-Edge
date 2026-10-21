function stage21a_estrada_jepson_microcases(runtimeDir, kittBoundaryDir, outFile)
% Verify the pinned public KITT Estrada-Jepson path on fixed micro-cases.
%
% runtimeDir contains an unmodified, filename-compatible copy of KITT's
% shipped v1.00 backup matcher.  KITT HEAD's advertised v1.01 file calls an
% absent helper for displacements beyond its one-pixel bootstrap, so it is
% audited but is not silently repaired here.

addpath(kittBoundaryDir);
addpath(runtimeDir);

params = struct('maxDist', 0.025);
n = 64;
diagLength = sqrt(2 * n * n);
tolerancePixels = params.maxDist * diagLength;

solution = false(n);
solution(32, 32) = true;
candidate = solution;
cases = runCase('exact_match', solution, candidate, params, true, 1, 1);

candidate = false(n);
candidate(32, 33) = true;
cases(end + 1) = runCase('one_pixel_offset', solution, candidate, params, true, 1, 1); %#ok<AGROW>

candidate = false(n);
candidate(32, 34) = true;
cases(end + 1) = runCase('inside_tolerance_two_pixels', solution, candidate, params, true, 1, 1); %#ok<AGROW>

candidate = false(n);
candidate(32, 35) = true;
cases(end + 1) = runCase('outside_tolerance_three_pixels', solution, candidate, params, true, 0, 0); %#ok<AGROW>

candidate = false(n);
candidate(32, 31) = true;
candidate(32, 33) = true;
cases(end + 1) = runCase('two_predictions_one_gt', solution, candidate, params, true, 1, 1); %#ok<AGROW>

solution2 = false(n);
solution2(32, 31) = true;
solution2(32, 33) = true;
candidate = false(n);
candidate(32, 32) = true;
cases(end + 1) = runCase('two_gt_one_prediction', solution2, candidate, params, true, 1, 1); %#ok<AGROW>

solution3 = false(n);
solution3(16:48, 32) = true;
solution3(32, 16:48) = true;
candidate = false(n);
candidate(16:48, 34) = true;
candidate(34, 16:48) = true;
cases(end + 1) = runCase('shifted_crossing_contours', solution3, candidate, params, false, 0.9, 0.9); %#ok<AGROW>

solutions = false(n, n, 2);
solutions(32, 32, 1) = true;
solutions(32, 40, 2) = true;
candidate = false(n);
candidate(32, 32) = true;
multiScores = oneToManyEJBC(solutions, candidate, params);
multi = struct();
multi.name = 'two_annotators_union_precision_accumulated_recall';
multi.f_measure = multiScores(1);
multi.precision = multiScores(2);
multi.recall = multiScores(3);
multi.expected_precision = 1;
multi.expected_recall = 0.5;
multi.expected_f_measure = 2 / 3;
multi.passed = abs(multi.precision - 1) < 1e-12 && ...
    abs(multi.recall - 0.5) < 1e-12 && ...
    abs(multi.f_measure - (2 / 3)) < 1e-12;

payload = struct();
payload.protocol = 'KITT Estrada-Jepson directional matching';
payload.max_dist_fraction_diagonal = params.maxDist;
payload.image_size = [n n];
payload.tolerance_pixels = tolerancePixels;
payload.cases = cases;
payload.multi_annotator_case = multi;
payload.observed_matching_semantics = struct( ...
    'directional_matching_is_asymmetric', true, ...
    'matching_is_not_one_to_one', true, ...
    'machine_precision_uses_union_across_annotations', true, ...
    'recall_accumulates_matches_and_gt_counts_across_annotations', true, ...
    'f_measure_alpha', 0.5);
payload.all_passed = all([cases.passed]) && multi.passed;

fid = fopen(outFile, 'w');
if fid == -1
    error('MFIEdge:Stage21AOutput', 'Could not open %s', outFile);
end
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s', jsonencode(payload, 'PrettyPrint', true));
end


function result = runCase(name, solution, candidate, params, exactExpected, minPrecision, minRecall)
[cm, residuals] = ejmBasedBinaryImageCM(solution, candidate, params);
result = struct();
result.name = name;
result.solution_pixels = sum(solution(:));
result.candidate_pixels = sum(candidate(:));
result.tp = cm(1, 1);
result.fp = cm(1, 2);
result.fn = cm(2, 1);
result.precision = residuals.prec;
result.recall = residuals.rec;
result.f_measure = residuals.F;
result.minimum_expected_precision = minPrecision;
result.minimum_expected_recall = minRecall;
if exactExpected
    result.passed = abs(result.precision - minPrecision) < 1e-12 && ...
        abs(result.recall - minRecall) < 1e-12;
else
    result.passed = result.precision >= minPrecision && result.recall >= minRecall;
end
end

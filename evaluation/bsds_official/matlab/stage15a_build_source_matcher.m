function stage15a_build_source_matcher(sourceDir, outDir)
% Build the pinned Berkeley correspondPixels sources outside the vendor tree.

if ~exist(outDir, 'dir')
    mkdir(outDir);
end

names = {'correspondPixels.cc', 'csa.cc', 'kofn.cc', 'match.cc', ...
    'Exception.cc', 'Matrix.cc', 'Random.cc', 'String.cc', 'Timer.cc'};
sources = cell(size(names));
for i = 1:numel(names)
    sources{i} = fullfile(sourceDir, names{i});
end
mex('-outdir', outDir, '-DNOBLAS', sources{:});

cfg = mex.getCompilerConfigurations('C++', 'Selected');
fid = fopen(fullfile(outDir, 'build_metadata.txt'), 'w');
if fid == -1
    error('MFIEdge:BuildMetadata', 'Could not write matcher build metadata.');
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'matlab=%s\n', version);
fprintf(fid, 'mexext=%s\n', mexext);
if isempty(cfg)
    fprintf(fid, 'compiler=unknown\n');
else
    fprintf(fid, 'compiler=%s\n', cfg.Name);
    fprintf(fid, 'compiler_version=%s\n', cfg.Version);
end
end

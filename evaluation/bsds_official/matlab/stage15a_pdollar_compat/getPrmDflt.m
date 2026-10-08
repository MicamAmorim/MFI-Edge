function varargout = getPrmDflt(args, defaults, checkExtra)
% Minimal compatibility shim for the frozen Stage-15a edgesEvalImg audit.
%
% Piotr Dollar's edges repository requires his separate Matlab toolbox for
% this parameter parser. The fixture diagnostic intentionally vendors
% neither that toolbox nor a moving checkout. This local shim implements
% only the documented name/value parsing used by edgesEvalImg and rejects
% unsupported forms instead of silently changing evaluator parameters.

if nargin < 3
    checkExtra = 0;
end
if ~iscell(args) || ~iscell(defaults) || mod(numel(defaults), 2) ~= 0
    error('MFIEdge:GetPrmDfltInput', 'Expected cell arguments and paired defaults.');
end

names = defaults(1:2:end);
values = defaults(2:2:end);
if mod(numel(args), 2) ~= 0
    error('MFIEdge:GetPrmDfltPairs', 'Parameters must be name/value pairs.');
end

for i = 1:2:numel(args)
    name = args{i};
    if ~(ischar(name) || (isstring(name) && isscalar(name)))
        error('MFIEdge:GetPrmDfltName', 'Parameter names must be text scalars.');
    end
    index = find(strcmp(char(name), names), 1);
    if isempty(index)
        if checkExtra
            error('MFIEdge:GetPrmDfltUnknown', 'Unknown parameter: %s', char(name));
        end
        continue;
    end
    values{index} = args{i + 1};
end

if nargout ~= numel(values)
    error('MFIEdge:GetPrmDfltOutputs', ...
        'Expected %d outputs for the registered defaults.', numel(values));
end
varargout = values;
end

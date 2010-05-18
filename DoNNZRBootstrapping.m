function DoNNZRBootstrapping(dirLoc)

    models = {'FullSet', 'SansWind', 'JustWind', 'Reflect', 'ZRBest'};
    statNames = {'corr', 'rmse', 'mae'};
    statFileStems = {'Corr', 'RMSE', 'MAE'};
    statNamesFull = {'Correlation Coefficient', ...
                     'Root Mean Squared Error [mm/hr]', ...
                     'Mean Absolute Error [mm/hr]'};
    statNamesTitle = {'Correlations', 'RMSEs', 'MAEs'};

    for statIndex = 1:length(statNames)
        [bootMeans, bootCIs] = BootstrapNNZR(dirLoc, statNames{statIndex}, models);

	save(fullfile(dirLoc, ['bootstrap_CI_' statFileStems{statIndex} '.txt']), 'bootCIs', '-ASCII')
	save(fullfile(dirLoc, ['bootstrap_Mean_' statFileStems{statIndex} '.txt']), 'bootMeans', '-ASCII')

        disp(bootCIs(:, 1));
        disp(bootMeans);
        disp(bootCIs(:, 2));
    end

function [bootMeans, bootCIs] = BootstrapNNZR(dirLoc, statName, models)
    bootMeans = zeros(length(models), 1);
    bootCIs = zeros(length(models), 2);

    for modelIndex = 1:length(models)
        [bootMeans(modelIndex), bootCIs(modelIndex, :)] = ProcessFile(fullfile(dirLoc, ['summary_' statName ...
                                                                                        '_' models{modelIndex} '.txt']));
    end


function [statBoot, statCI] = ProcessFile(fileName)

    C = load(fileName, '-ASCII');

    statBoot = mean(bootstrp(2000, @mean, C));
    statCI = bootci(2000, {@mean, C}, 'alpha', 0.1, 'type', 'bca');    % does the 90 percentile interval using BCa


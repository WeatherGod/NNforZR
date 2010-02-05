function DoNNZRBootstrapping(dirLoc)

    models = {'FullSet', 'SansWind', 'JustWind', 'Reflect', 'ZRBest'};
    statNames = {'corr', 'rmse', 'mae'};
    statNamesFull = {'Correlation Coefficient', 'Root Mean Squared Error [mm/hr]', 'Mean Absolute Error [mm/hr]'};
    statNamesTitle = {'Correlations', 'RMSEs', 'MAEs'};

    for statIndex = 1:length(statNames)
        bootMeans = zeros(length(models), 1);
        bootCIs = zeros(length(models), 2);

        for modelIndex = 1:length(models)
            [bootMeans(modelIndex), bootCIs(modelIndex, :)] = ProcessFile(fullfile(dirLoc, ['summary_' statNames{statIndex} ...
                                                                                            '_' models{modelIndex} '.txt']));
        end
    
        %h = axes('Position',[0 0 1 1],'Visible','off');
        %axes('Position',[.1 .1 .8 .8]);
        disp(bootCIs(:, 1));
        disp(bootMeans);
        disp(bootCIs(:, 2));
    
        figure;
        errorbar(1:length(models), bootMeans, bootMeans - bootCIs(:, 1), ...
                                              bootCIs(:, 2) - bootMeans, ...
                                   '.k', 'LineWidth', 1.5, 'MarkerSize', 20);
 
        set(gca, 'XTick', 1:length(models), 'XTickLabel', models);
        ylabel(statNamesFull{statIndex}, 'FontSize', 12);
        xlabel('Models', 'FontSize', 12);
        title(['Mean Model ' statNamesTitle{statIndex}], 'FontSize', 13);
    end
                                                                           


function [statBoot, statCI] = ProcessFile(fileName)

    C = load(fileName, '-ascii');

    statBoot = mean(bootstrp(2000, @mean, C));
    statCI = bootci(2000, {@mean, C}, 'alpha', 0.1, 'type', 'bca');    % does the 90 percentile interval using BCa

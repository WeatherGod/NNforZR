function Paper_BootstrapFig(dirLoc, outputFormat)

    models = {'FullSet', 'SansWind', 'JustWind', 'Reflect', 'ZRBest'};
    statNames = {'corr', 'rmse', 'mae'};
    statFileStems = {'Corr', 'RMSE', 'MAE'};
    statNamesFull = {'Correlation Coefficient', ...
                     'Root Mean Squared Error [mm/hr]', ...
                     'Mean Absolute Error [mm/hr]'};
    statNamesTitle = {'Correlations', 'RMSEs', 'MAEs'};

    figure;

    for statIndex = 1:length(statNames)

        bootCIs = load(fullfile(dirLoc, ['bootstrap_CI_' statFileStems{statIndex} '.txt']), '-ASCII')
        bootMeans = load(fullfile(dirLoc, ['bootstrap_Mean_' statFileStems{statIndex} '.txt']), '-ASCII')

	disp(bootCIs(:, 1));
        disp(bootMeans);
        disp(bootCIs(:, 2));

        subplot(1, length(statNames), statIndex)
        MakeErrorBars(bootMeans, bootCIs, models);

        ylabel(statNamesFull{statIndex}, 'FontSize', 11);
        xlabel('Models', 'FontSize', 11);
        title(['Mean Model ' statNamesTitle{statIndex}], 'FontSize', 12);
                                           
%        saveas(gcf, ['Models' statFileStems{statIndex} '_Raw.' outputFormat]);
    end

    saveas(gcf, ['ModelPerformances.' outputFormat])


function figHandle = MakeErrorBars(bootMeans, bootCIs, models)    
    errorbar(1:length(models), bootMeans, bootMeans - bootCIs(:, 1), ...
                                          bootCIs(:, 2) - bootMeans, ...
                               '.k', 'LineWidth', 1.5, 'MarkerSize', 20);
 
    set(gca, 'XTick', 1:length(models), 'XTickLabel', models);



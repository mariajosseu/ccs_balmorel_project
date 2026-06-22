#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import os
import pandas as pd
import numpy as np
from typing import Union
import matplotlib.pyplot as plt
from ..formatting import balmorel_colours
import matplotlib.dates as mdates
from typing import Tuple, List
import matplotlib.patches as mpatches

#%% ------------------------------- ###
###       1. Bar chart function     ###
### ------------------------------- ###


def plot_bar_chart(df: pd.core.frame.DataFrame, filter: dict, series: Union[str, list], categories: Union[str, list],
                    title: tuple, size: tuple, xaxis: tuple, yaxis: tuple, legend: tuple, series_order: dict, categories_order:dict,
                    save: bool, namefile: str, plot_style: str = 'light'):
    """
    Plotting function for the bar chart

    Args:
        df (DataFrame): Dataframe with the result
        filter (dict): Dictionary with the filters to apply
        table (str): Table selected in the result file
        series (Union[str, list]): Columns used as series
        categories (Union[str, list]): Columns used as categories
        title (tuple): Plot title and size
        size (tuple): Size of the plot
        xaxis (tuple): Options for the x axis
        yaxis (tuple): Options for the y axis
        legend (tuple): Options for the legend
        series_order (dict): Order of the index
        categories_order (dict): Order of the stacking
        save (bool): Do the plot have to be saved
        namefile (str): Name of the saved file
        plot_style (str): Style of the plot, light or dark. Defaults to light
    """
    
    # Unit
    if 'Unit' in df.columns:
        unit = df['Unit'][0]  # Get the first unit value if the column exists
    else:
        unit = None  # Set to an empty list

    # Continue with unit_dict as normal
    unit_dict = {'GW': 'Capacity', 'TWh': 'Energy', 'GWh': 'Energy'}

    # Filtering the dataframe 
    query_parts = []
    for key, value in filter.items():
        if isinstance(value, list):
            values_str = ', '.join([f'"{v}"' for v in value])
            query_parts.append(f'{key} in [{values_str}]')
        else:
            query_parts.append(f'{key} {value}')
    query_str = ' & '.join(query_parts)
    df = df.query(query_str)
    
    if series : 

        # Pivot
        temp = df.pivot_table(index=series,
                        columns=categories,
                        values='Value',
                        aggfunc='sum').fillna(0)
        
        # Ordering the index
        order_list = []
        for serie, order in series_order.items() :
            serie_string = f'{serie}_order'
            order_list.append(serie_string)
            # To make sure we give an order when the user does not specify it
            if len(order) >= 1 :
                used_order = order
            else : 
                used_order = temp.index.get_level_values(serie).unique()
            # Creating a column for ordering
            temp[serie_string] = temp.index.get_level_values(serie).map({value: idx for idx, value in enumerate(used_order)})
        # Ordering with the columns created
        temp = temp.sort_values(by=order_list)
        temp = temp.drop(columns=order_list)

        if len(categories) >= 1 and len(categories_order) >= 1 :
            # Ordering the categories
            order_list = []
            if len(categories_order) == 1 :
                for categorie, order in categories_order.items():
                    order_list = order_list + order
                all_categories = temp.columns.tolist()
                for element in all_categories :
                    if element not in order_list :
                        order_list.append(element)
                # Make sure we don't have the element if they are not there :
                order_list = [item for item in order_list if item in all_categories]
            elif len(categories_order) >= 1 :
                # Create a dictionary for fast look-up of index
                order_index = []
                all_categories = temp.columns.tolist()
                i = 0
                for categorie, order in categories_order.items():
                    ordered_index = {value: index for index, value in enumerate(order)}
                    index_nb = len(ordered_index)
                    for item in all_categories :
                        if item[i] not in list(ordered_index.keys()) :
                            ordered_index[item[i]] = index_nb
                            index_nb += 1 
                    order_index.append(ordered_index)
                    i += 1
                
                # Custom key function for sorting
                def custom_sort_key(item):
                    if len(item) == 2 :
                        first_value, second_value = item
                        return (order_index[0][first_value], order_index[1][second_value])
                    if len(item) == 3 :
                        first_value, second_value, third_value = item
                        return (order_index[0][first_value], order_index[1][second_value], order_index[2][third_value])

                # Sort the list
                order_list = sorted(all_categories, key=custom_sort_key)
                
            temp = temp[order_list]
        
        #Sometimes one instance of index combination is missing and it's creating plotting issue. For now we'll complete by 0 this instance.
        # if type(temp.index[0]) == list:
        #     all_combinations = pd.MultiIndex.from_product([temp.index.get_level_values(i).unique() for i in range(len(temp.index[0]))], names=series)
        #     temp = temp.reindex(all_combinations).reset_index()
        #     temp = df.pivot_table(index=series,
        #                     columns=categories,
        #                     values='Value',
        #                     aggfunc='sum',
        #                     dropna=False).fillna(0)
        
        max_bar = temp.sum(axis=1).max()
        
        # Object oriented plotting
        fig, ax = plt.subplots(figsize=size)
        transform_to_axes = ax.transData + ax.transAxes.inverted()
        
        # Colors 
        try:
            temp.plot(ax=ax, kind='bar', stacked=True, legend=False, color=balmorel_colours)
        except KeyError:
            temp.plot(ax=ax, kind='bar', stacked=True, legend=False)
        
        if legend[0] == True:
            # To deal with double legend
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(legend[2], legend[3]), loc=legend[1], ncols=legend[4], reverse=True)
        
        # Customizing x-axis
        dict_fw = {True:'bold',False:'normal'}
        categories_first = temp.index.get_level_values(-1).unique()
        ax.set_xticks(range(len(temp)))
        if xaxis[0]==True :
            if type(temp.index[0]) != str:
                ax.set_xticklabels([f'{i[-1]}' for i in temp.index], fontsize=xaxis[1], fontweight=dict_fw[xaxis[2]], rotation=0, ha='center')
            else :
                ax.set_xticklabels([f'{i}' for i in temp.index], fontsize=xaxis[1], fontweight=dict_fw[xaxis[2]], rotation=0, ha='center')
        else :
            ax.set_xticklabels([f'' for i in temp.index])

        # Add x-axis labels for double stage
        if plot_style == 'dark':
            line_colour = 'white'
        else:
            line_colour = 'black'
            
        if type(temp.index[0]) == tuple and len(temp.index[0]) == 2 :
            categories_second = temp.index.get_level_values(-2).unique()
            category_positions_second = [temp.index.get_level_values(-2).tolist().index(cat) for cat in categories_second]
            
            for ind, cat in enumerate(categories_second):
                if xaxis[3]==True :
                    try :
                        x_data_coord = (category_positions_second[ind] + category_positions_second[ind+1]-1)/2
                    except IndexError :
                        x_data_coord = (category_positions_second[ind] + len(temp)-1)/2
                    x_ax_coord = transform_to_axes.transform((x_data_coord, 0))[0]
                    ax.text(x_ax_coord, xaxis[4]*0.01, cat, ha='center', va='center', fontsize=xaxis[5], fontweight=dict_fw[xaxis[6]], rotation=0, transform=ax.transAxes)
                    if ind != 0 :
                        x_data_coord = category_positions_second[ind]-0.5
                        x_ax_coord = transform_to_axes.transform((x_data_coord, 0))[0]
                        line = plt.Line2D([x_ax_coord, x_ax_coord], [xaxis[7]*xaxis[4]*0.01, 0], transform=ax.transAxes, clip_on=False, color=line_colour, linestyle='-', linewidth=1)
                        ax.add_line(line)
                
        # Add x-axis labels for triple stage
        if type(temp.index[0]) == tuple and len(temp.index[0]) == 3 :
            categories_third = temp.index.get_level_values(-3).unique()
            category_positions_third = [temp.index.get_level_values(-3).tolist().index(cat) for cat in categories_third]
            categories_second = temp.index.get_level_values(-2).tolist()
            
            for ind3, cat3 in enumerate(categories_third):
                if xaxis[8]==True :
                    try :
                        x_data_coord = (category_positions_third[ind3] + category_positions_third[ind3+1]-1)/2
                    except IndexError :
                        x_data_coord = (category_positions_third[ind3] + len(temp)-1)/2
                    x_ax_coord = transform_to_axes.transform((x_data_coord, 0))[0]
                    ax.text(x_ax_coord, xaxis[9]*0.01, cat3, ha='center', va='center', fontsize=xaxis[10], fontweight=dict_fw[xaxis[11]], rotation=0, transform=ax.transAxes)
                    if ind3 != 0 :
                        x_data_coord = category_positions_third[ind3]-0.5
                        x_ax_coord = transform_to_axes.transform((x_data_coord, 0))[0]
                        line = plt.Line2D([x_ax_coord, x_ax_coord], [xaxis[12]*xaxis[9]*0.01, -0.001], transform=ax.transAxes, clip_on=False, color=line_colour, linestyle='-', linewidth=1)
                        ax.add_line(line)
                
                if xaxis[3]==True :     
                    ind21, ind22 = category_positions_third[ind3], category_positions_third[ind3]
                    try :
                        next = category_positions_third[ind3+1]
                    except IndexError :
                        next = len(temp)
                    while ind21 != next :
                        if ind22+1 == next or categories_second[ind22] != categories_second[ind22+1] :
                            x_data_coord = (ind21 + ind22)/2
                            x_ax_coord = transform_to_axes.transform((x_data_coord, 0))[0]
                            ax.text(x_ax_coord, xaxis[4]*0.01, categories_second[ind21], ha='center', va='center', fontsize=xaxis[5], fontweight=dict_fw[xaxis[6]], rotation=0, transform=ax.transAxes)
                            ind21 = ind22+1
                            ind22 += 1
                            if ind21 != 0 and ind21 != next:
                                x_ax_coord = transform_to_axes.transform((ind21-0.5, 0))[0]
                                line = plt.Line2D([x_ax_coord, x_ax_coord], [xaxis[7]*xaxis[4]*0.01, 0], transform=ax.transAxes, clip_on=False, color=line_colour, linestyle='-', linewidth=1)
                                ax.add_line(line)
                        else :
                            ind22 += 1
        
        # Y label
        if yaxis[0] != '':
            ax.set_ylabel(yaxis[0])
        else :
            if unit in unit_dict:
                ax.set_ylabel(f'{unit_dict[unit]} ({unit})', fontsize=yaxis[1])
            elif unit==None:
                ax.set_ylabel(f'Value', fontsize=yaxis[1])
            else :
                ax.set_ylabel(f'Value ({unit})', fontsize=yaxis[1])
                
        if yaxis[2] != yaxis[3]:
            ax.set_ylim(yaxis[2],yaxis[3])
        
        ax.set_xlabel('')
        
        ax.set_title(title[0], fontsize=title[1])
        
        if plot_style == 'dark':
            plt.style.use('dark_background')
            ax.set_facecolor('none')
            transparent = True
        else:
            transparent = False
        
        if save == True :
            # Ensure the 'output' directory exists
            output_dir = 'output'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            if '.' not in namefile:
                namefile += '.png'
                
            output_path = os.path.join(output_dir, namefile)
            plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=transparent)
        
        return fig
    



def plot_emissions_grid_by_year_and_scenario(
    emissions_df: pd.DataFrame, years: list = None, scenarios: list = None
):
    """Plot emissions in a 2x2 grid (years as columns, scenarios as rows), grouped by fuel.

    Args:
        emissions_df (pd.DataFrame): Emissions results dataframe.
        years (list, optional): Years to plot. Defaults to all available.
        scenarios (list, optional): Scenarios to plot. Defaults to all available.

    Returns:
        tuple[plt.Figure, np.ndarray]: The figure and axes array.
    """
    # Get available years and scenarios
    if years is None:
        years = sorted(emissions_df["Y"].unique())
    else:
        years = [str(y) for y in years]  # Convert to strings to match data

    if scenarios is None:
        scenarios = sorted(emissions_df["Scenario"].unique())

    # Create 2x2 grid (rows=scenarios, columns=years)
    fig, axes = plt.subplots(len(scenarios), len(years), figsize=(14, 9))
    if len(scenarios) == 1 and len(years) == 1:
        axes = np.array([[axes]])
    elif len(scenarios) == 1:
        axes = axes.reshape(1, -1)
    elif len(years) == 1:
        axes = axes.reshape(-1, 1)

    # Plot each combination
    for i, scenario in enumerate(scenarios):
        for j, year in enumerate(years):
            ax = axes[i, j]

            # Filter data for this scenario and year
            filtered = emissions_df[
                (emissions_df["Scenario"] == scenario) & (emissions_df["Y"] == year)
            ]

            if not filtered.empty:
                # Group by fuel type and sum emissions
                fuel_emissions = filtered.groupby("FFF")["Value"].sum().sort_values()

                # Plot as horizontal bar chart for better readability
                colors = ["red" if v < 0 else "green" for v in fuel_emissions.values]
                ax.barh(
                    range(len(fuel_emissions)),
                    fuel_emissions.values,
                    color=colors,
                    alpha=0.7,
                )
                ax.set_yticks(range(len(fuel_emissions)))
                ax.set_yticklabels(fuel_emissions.index, fontsize=9)
                ax.axvline(0, color="black", linewidth=0.8)

            ax.set_title(f"{scenario} - {year}", fontsize=11, fontweight="bold")
            ax.set_xlabel("Emissions (kton)" if j == 0 else "", fontsize=9)
            ax.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()
    return fig, axes
            
        
def plot_emissions_grid_by_year_and_scenario(
    emissions_df: pd.DataFrame, years: list = None, scenarios: list = None
):
    """Plot emissions in a 2x2 grid (years as columns, scenarios as rows), grouped by fuel.

    Args:
        emissions_df (pd.DataFrame): Emissions results dataframe.
        years (list, optional): Years to plot. Defaults to all available.
        scenarios (list, optional): Scenarios to plot. Defaults to all available.

    Returns:
        tuple[plt.Figure, np.ndarray]: The figure and axes array.
    """
    # Get available years and scenarios
    if years is None:
        years = sorted(emissions_df["Y"].unique())
    else:
        years = [str(y) for y in years]  # Convert to strings to match data

    if scenarios is None:
        scenarios = sorted(emissions_df["Scenario"].unique())

    # Create 2x2 grid (rows=scenarios, columns=years)
    fig, axes = plt.subplots(len(scenarios), len(years), figsize=(14, 9))
    if len(scenarios) == 1 and len(years) == 1:
        axes = np.array([[axes]])
    elif len(scenarios) == 1:
        axes = axes.reshape(1, -1)
    elif len(years) == 1:
        axes = axes.reshape(-1, 1)

    # Plot each combination
    for i, scenario in enumerate(scenarios):
        for j, year in enumerate(years):
            ax = axes[i, j]

            # Filter data for this scenario and year
            filtered = emissions_df[
                (emissions_df["Scenario"] == scenario) & (emissions_df["Y"] == year)
            ]

            if not filtered.empty:
                # Group by fuel type and sum emissions
                fuel_emissions = filtered.groupby("FFF")["Value"].sum().sort_values()

                # Plot as horizontal bar chart for better readability
                colors = ["red" if v < 0 else "green" for v in fuel_emissions.values]
                ax.barh(
                    range(len(fuel_emissions)),
                    fuel_emissions.values,
                    color=colors,
                    alpha=0.7,
                )
                ax.set_yticks(range(len(fuel_emissions)))
                ax.set_yticklabels(fuel_emissions.index, fontsize=9)
                ax.axvline(0, color="black", linewidth=0.8)

            ax.set_title(f"{scenario} - {year}", fontsize=11, fontweight="bold")
            ax.set_xlabel("Emissions (kton)" if j == 0 else "", fontsize=9)
            ax.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()
    return fig, axes


def plot_capacity_pie_by_scenario(
    capacity_df: pd.DataFrame,
    year: int = None,
    scenarios: list = None,
    min_capacity: float = 0.0,
):
    """
    Plot installed capacity mix as pie charts:
    one pie chart per scenario.

    Technologies whose name contains 'storage' are removed.

    Args:
        capacity_df (pd.DataFrame): Installed capacity results dataframe.
        year (int, optional): Year to plot. If None, uses all years.
        scenarios (list, optional): Scenarios to plot. Defaults to all available.
        min_capacity (float, optional): Minimum total technology capacity to show.
            Technologies below this total are grouped as 'Other'.

    Returns:
        tuple[plt.Figure, np.ndarray]: The figure and axes.
    """

    generation_tech_color = {
        "HYDRO-RESERVOIRS": "#33b1ff",
        "HYDRO-RUN-OF-RIVER": "#4589ff",
        "HYDRO": "#33b1ff",
        "WIND-ONSHORE": "#006460",
        "BOILERS": "#8B008B",
        "ELECT-TO-HEAT": "#FFA500",
        "INTERSEASONAL-HEAT-STORAGE": "#FFD700",
        "CHP-BACK-PRESSURE": "#E5D8D8",
        "SMR-CCS": "#00BFFF",
        "SMR": "#d1b9b9",
        "INTRASEASONAL-HEAT-STORAGE": "#00FFFF",
        "CONDENSING": "#8a3ffc",
        "SOLAR-HEATING": "#FF69B4",
        "CHP-EXTRACTION": "#ff7eb6",
        "SOLAR-PV": "#d2a106",
        "WIND-OFFSHORE": "#08bdba",
        "INTRASEASONAL-ELECT-STORAGE": "#ba4e00",
        "ELECTROLYZER": "#ADD8E6",
        "H2-STORAGE": "#FFC0CB",
        "FUELCELL": "#d4bbff",
        "CHP": "#E5D8D8",
    }

    df = capacity_df.copy()

    # Remove all technologies containing "storage"
    df = df[
        ~df["Technology"]
        .astype(str)
        .str.lower()
        .str.contains("storage", na=False)
    ]

    df["Scenario_clean"] = df["Scenario"].astype(str).str.strip()
    df["Scenario_key"] = df["Scenario_clean"].str.lower()
    df["Year"] = df["Year"].astype(int)

    if year is not None:
        year = int(year)
        df = df[df["Year"] == year]

    if scenarios is None:
        scenarios = sorted(df["Scenario_clean"].unique())
    else:
        scenario_keys = [str(s).strip().lower() for s in scenarios]
        df = df[df["Scenario_key"].isin(scenario_keys)]

        scenario_order = {
            str(s).strip().lower(): str(s).strip()
            for s in scenarios
        }

        df["Scenario_clean"] = df["Scenario_key"].map(scenario_order)

    plot_df = (
        df.groupby(["Scenario_clean", "Technology"])["Value"]
        .sum()
        .reset_index()
    )

    # Remove zero or negative capacities
    plot_df = plot_df[plot_df["Value"] > 0]

    if plot_df.empty:
        raise ValueError("No positive capacity values available after filtering.")

    # Number of pie charts
    n_scenarios = len(scenarios) if scenarios is not None else plot_df["Scenario_clean"].nunique()

    n_cols = min(2, n_scenarios)
    n_rows = int(np.ceil(n_scenarios / n_cols))

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(6.5 * n_cols, 5.0 * n_rows), # Slightly widened the figure
    )

    axes = np.array(axes).reshape(-1)

    if scenarios is None:
        scenario_list = sorted(plot_df["Scenario_clean"].unique())
    else:
        scenario_list = [str(s).strip() for s in scenarios]

    all_legend_handles = {}
    fallback_color = "#B0B0B0"
    
    # --- Custom function to hide overlaps by dropping small labels ---
    def autopct_generator(limit):
        def inner_autopct(pct):
            return f"{pct:.1f}%" if pct > limit else ""
        return inner_autopct
    # -----------------------------------------------------------------

    for idx, scenario in enumerate(scenario_list):
        ax = axes[idx]

        scenario_df = plot_df[plot_df["Scenario_clean"] == scenario]

        if scenario_df.empty:
            ax.text(
                0.5,
                0.5,
                "No data",
                ha="center",
                va="center",
                fontsize=10,
            )
            ax.set_title(scenario, fontsize=11, fontweight="bold")
            ax.axis("off")
            continue

        technology_capacity = (
            scenario_df.groupby("Technology")["Value"]
            .sum()
            .sort_values(ascending=False)
        )

        # Group small technologies into "Other"
        small_techs = technology_capacity[technology_capacity < min_capacity]

        if not small_techs.empty:
            large_techs = technology_capacity[technology_capacity >= min_capacity]
            technology_capacity = pd.concat(
                [
                    large_techs,
                    pd.Series({"Other": small_techs.sum()}),
                ]
            )

        colors = []
        for technology in technology_capacity.index:
            technology_key = str(technology).strip().upper()
            colors.append(generation_tech_color.get(technology_key, fallback_color))

        wedges, texts, autotexts = ax.pie(
            technology_capacity.values,
            labels=None,
            autopct=autopct_generator(3.0), # Only shows percentages greater than 3.0%
            startangle=90,
            colors=colors,
            textprops={"fontsize": 8},
        )

        for tech, wedge in zip(technology_capacity.index, wedges):
            # Only add to legend if not already there, keeps dictionary clean
            if tech not in all_legend_handles:
                all_legend_handles[tech] = wedge

        total_capacity = technology_capacity.sum()

        title = f"{scenario}"
        if year is not None:
            title += f" - {year}"
        title += f"\nTotal: {total_capacity:.2f} GW"

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.axis("equal")

    # Turn off unused subplots
    for idx in range(len(scenario_list), len(axes)):
        axes[idx].axis("off")

    main_title = "Installed Capacity Mix by Scenario"
    if year is not None:
        main_title += f" - {year}"

    fig.suptitle(main_title, fontsize=14, fontweight="bold", y=0.98)

    # Allow room for the legend on the right edge by squeezing subplots to the left
    plt.tight_layout(rect=[0, 0, 0.85, 0.95]) 

    # --- Fixed Legend Parameters ---
    fig.legend(
        all_legend_handles.values(),
        all_legend_handles.keys(),
        title="Technology",
        bbox_to_anchor=(0.85, 0.5), # Anchor at the 85% mark on the x-axis
        loc="center left",          # The left side of the legend aligns with the anchor
        fontsize=9,
    )
    # -------------------------------

    return fig, axes


def plot_capacity_pie_by_scenario(
    capacity_df: pd.DataFrame,
    year: int = None,
    scenarios: list = None,
    min_capacity: float = 0.0,
):
    """
    Plot installed capacity mix as pie charts:
    one pie chart per scenario.

    Technologies whose name contains 'storage' are removed.

    Args:
        capacity_df (pd.DataFrame): Installed capacity results dataframe.
        year (int, optional): Year to plot. If None, uses all years.
        scenarios (list, optional): Scenarios to plot. Defaults to all available.
        min_capacity (float, optional): Minimum total technology capacity to show.
            Technologies below this total are grouped as 'Other'.

    Returns:
        tuple[plt.Figure, np.ndarray]: The figure and axes.
    """

    generation_tech_color = {
        "HYDRO-RESERVOIRS": "#33b1ff",
        "HYDRO-RUN-OF-RIVER": "#4589ff",
        "HYDRO": "#33b1ff",
        "WIND-ONSHORE": "#006460",
        "BOILERS": "#8B008B",
        "ELECT-TO-HEAT": "#FFA500",
        "INTERSEASONAL-HEAT-STORAGE": "#FFD700",
        "CHP-BACK-PRESSURE": "#E5D8D8",
        "SMR-CCS": "#00BFFF",
        "SMR": "#d1b9b9",
        "INTRASEASONAL-HEAT-STORAGE": "#00FFFF",
        "CONDENSING": "#8a3ffc",
        "SOLAR-HEATING": "#FF69B4",
        "CHP-EXTRACTION": "#ff7eb6",
        "SOLAR-PV": "#d2a106",
        "WIND-OFFSHORE": "#08bdba",
        "INTRASEASONAL-ELECT-STORAGE": "#ba4e00",
        "ELECTROLYZER": "#ADD8E6",
        "H2-STORAGE": "#FFC0CB",
        "FUELCELL": "#d4bbff",
        "CHP": "#E5D8D8",
    }

    df = capacity_df.copy()

    # Remove all technologies containing "storage"
    df = df[
        ~df["Technology"]
        .astype(str)
        .str.lower()
        .str.contains("storage", na=False)
    ]

    df["Scenario_clean"] = df["Scenario"].astype(str).str.strip()
    df["Scenario_key"] = df["Scenario_clean"].str.lower()
    df["Year"] = df["Year"].astype(int)

    if year is not None:
        year = int(year)
        df = df[df["Year"] == year]

    if scenarios is None:
        scenarios = sorted(df["Scenario_clean"].unique())
    else:
        scenario_keys = [str(s).strip().lower() for s in scenarios]
        df = df[df["Scenario_key"].isin(scenario_keys)]

        scenario_order = {
            str(s).strip().lower(): str(s).strip()
            for s in scenarios
        }

        df["Scenario_clean"] = df["Scenario_key"].map(scenario_order)

    plot_df = (
        df.groupby(["Scenario_clean", "Technology"])["Value"]
        .sum()
        .reset_index()
    )

    # Remove zero or negative capacities
    plot_df = plot_df[plot_df["Value"] > 0]

    if plot_df.empty:
        raise ValueError("No positive capacity values available after filtering.")

    # Number of pie charts
    n_scenarios = len(scenarios) if scenarios is not None else plot_df["Scenario_clean"].nunique()

    n_cols = min(2, n_scenarios)
    n_rows = int(np.ceil(n_scenarios / n_cols))

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(6.5 * n_cols, 5.0 * n_rows), # Slightly widened the figure
    )

    axes = np.array(axes).reshape(-1)

    if scenarios is None:
        scenario_list = sorted(plot_df["Scenario_clean"].unique())
    else:
        scenario_list = [str(s).strip() for s in scenarios]

    all_legend_handles = {}
    fallback_color = "#B0B0B0"
    
    # --- Custom function to hide overlaps by dropping small labels ---
    def autopct_generator(limit):
        def inner_autopct(pct):
            return f"{pct:.1f}%" if pct > limit else ""
        return inner_autopct
    # -----------------------------------------------------------------

    for idx, scenario in enumerate(scenario_list):
        ax = axes[idx]

        scenario_df = plot_df[plot_df["Scenario_clean"] == scenario]

        if scenario_df.empty:
            ax.text(
                0.5,
                0.5,
                "No data",
                ha="center",
                va="center",
                fontsize=10,
            )
            ax.set_title(scenario, fontsize=11, fontweight="bold")
            ax.axis("off")
            continue

        technology_capacity = (
            scenario_df.groupby("Technology")["Value"]
            .sum()
            .sort_values(ascending=False)
        )

        # Group small technologies into "Other"
        small_techs = technology_capacity[technology_capacity < min_capacity]

        if not small_techs.empty:
            large_techs = technology_capacity[technology_capacity >= min_capacity]
            technology_capacity = pd.concat(
                [
                    large_techs,
                    pd.Series({"Other": small_techs.sum()}),
                ]
            )

        colors = []
        for technology in technology_capacity.index:
            technology_key = str(technology).strip().upper()
            colors.append(generation_tech_color.get(technology_key, fallback_color))

        wedges, texts, autotexts = ax.pie(
            technology_capacity.values,
            labels=None,
            autopct=autopct_generator(3.0), # Only shows percentages greater than 3.0%
            startangle=90,
            colors=colors,
            textprops={"fontsize": 8},
        )

        for tech, wedge in zip(technology_capacity.index, wedges):
            # Only add to legend if not already there, keeps dictionary clean
            if tech not in all_legend_handles:
                all_legend_handles[tech] = wedge

        total_capacity = technology_capacity.sum()

        title = f"{scenario}"
        if year is not None:
            title += f" - {year}"
        title += f"\nTotal: {total_capacity:.2f} GW"

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.axis("equal")

    # Turn off unused subplots
    for idx in range(len(scenario_list), len(axes)):
        axes[idx].axis("off")

    main_title = "Installed Capacity Mix by Scenario"
    if year is not None:
        main_title += f" - {year}"

    fig.suptitle(main_title, fontsize=14, fontweight="bold", y=0.98)

    # Allow room for the legend on the right edge by squeezing subplots to the left
    plt.tight_layout(rect=[0, 0, 0.85, 0.95]) 

    # --- Fixed Legend Parameters ---
    fig.legend(
        all_legend_handles.values(),
        all_legend_handles.keys(),
        title="Technology",
        bbox_to_anchor=(0.85, 0.5), # Anchor at the 85% mark on the x-axis
        loc="center left",          # The left side of the legend aligns with the anchor
        fontsize=9,
    )
    # -------------------------------

    return fig, axes


# def create_balmorel_datetime_df(
#     year: int,
#     n_seasons: int = 52,
#     season_col: str = "Season",
#     time_col: str = "Time",
# ):
#     """
#     Create a Balmorel-like SSS/TTT datetime mapping.

#     Assumes:
#         Season values look like S01, S02, ...
#         Time values look like T001, T002, ...
#     """

#     datetime_index = pd.date_range(
#         start=f"{year}-01-01 00:00:00",
#         end=f"{year}-12-31 23:00:00",
#         freq="h",
#     )

#     time_df = pd.DataFrame({"DATETIME": datetime_index})

#     time_df["Year"] = time_df["DATETIME"].dt.year
#     time_df["Month"] = time_df["DATETIME"].dt.month
#     time_df["Day"] = time_df["DATETIME"].dt.day
#     time_df["Hour"] = time_df["DATETIME"].dt.hour + 1
#     time_df["HourOfYear"] = np.arange(1, len(time_df) + 1)

#     time_df["Season_num"] = (
#         ((time_df["HourOfYear"] - 1) * n_seasons // len(time_df)) + 1
#     )

#     time_df["Time_num"] = (
#         time_df
#         .groupby("Season_num")
#         .cumcount()
#         + 1
#     )

#     time_df[season_col] = "S" + time_df["Season_num"].astype(str).str.zfill(2)
#     time_df[time_col] = "T" + time_df["Time_num"].astype(str).str.zfill(3)

#     return time_df[
#         [
#             "DATETIME",
#             "Year",
#             "Month",
#             "Day",
#             "Hour",
#             "HourOfYear",
#             "Season_num",
#             "Time_num",
#             season_col,
#             time_col,
#         ]
#     ]


def plot_generation_stacked_by_technology_per_scenario(
    generation_df: pd.DataFrame,
    scenarios: list = None,
    year: int = None,
    country: str = None,
    region: str = None,
    area: str = None,
    min_value: float = 0.0,
    n_seasons: int = 52,
):
    """
    Plot generation/value over time as stacked area plots, one plot per scenario.
    The stack is grouped by Generation.

    The function creates a full Balmorel SSS/TTT datetime mapping and merges it
    into the results, so the x-axis covers the whole year even when some
    Season-Time combinations have no data.

    If the generation name starts with 'BIO', it is plotted in green.
    Otherwise, it is plotted in blue.
    """

    if year is None:
        raise ValueError("You must provide year to create the full Balmorel datetime axis.")

    df = generation_df.copy()

    df["Scenario_clean"] = df["Scenario"].astype(str).str.strip()
    df["Scenario_key"] = df["Scenario_clean"].str.lower()
    df["Generation"] = df["Generation"].astype(str).str.strip()
    df["Year"] = df["Year"].astype(int)

    df["Season"] = df["Season"].astype(str).str.strip()
    df["Time"] = df["Time"].astype(str).str.strip()

    # Optional filters
    df = df[df["Year"] == int(year)]

    if country is not None:
        df = df[df["Country"].astype(str).str.upper() == country.upper()]

    if region is not None:
        df = df[df["Region"].astype(str).str.upper() == region.upper()]

    if area is not None:
        df = df[df["Area"].astype(str).str.upper() == area.upper()]

    if scenarios is None:
        scenario_list = sorted(df["Scenario_clean"].unique())
    else:
        scenario_keys = [str(s).strip().lower() for s in scenarios]
        df = df[df["Scenario_key"].isin(scenario_keys)]

        scenario_order = {
            str(s).strip().lower(): str(s).strip()
            for s in scenarios
        }

        df["Scenario_clean"] = df["Scenario_key"].map(scenario_order)
        scenario_list = [str(s).strip() for s in scenarios]

    if df.empty:
        raise ValueError("No data available after filtering.")

    # # Create full Balmorel time mapping
    # time_df = create_balmorel_datetime_df(
    #     year=year,
    #     n_seasons=n_seasons,
    #     season_col="Season",
    #     time_col="Time",
    # )

    # full_datetime_axis = time_df[["DATETIME", "Season", "Time"]].copy()

    # # Merge DATETIME into generation dataframe
    # df = df.merge(
    #     time_df[["DATETIME", "Season", "Time"]],
    #     on=["Season", "Time"],
    #     how="left",
    # )

    # Remove rows that did not match the Balmorel time structure
    df = df.dropna(subset=["DATETIME"])

    # Remove zero or negative values only for stacked values
    df = df[df["Value"] > 0]

    if df.empty:
        raise ValueError("No positive generation values available after filtering.")

    figures = {}

    for scenario in scenario_list:
        scenario_df = df[df["Scenario_clean"] == scenario].copy()

        if scenario_df.empty:
            continue

        # Aggregate by datetime and generation unit
        plot_df = (
            scenario_df
            .groupby(["DATETIME", "Generation"], as_index=False)["Value"]
            .sum()
            .sort_values("DATETIME")
        )

        pivot_df = (
            plot_df
            .pivot_table(
                index="DATETIME",
                columns="Generation",
                values="Value",
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )

        # # Fill the whole year using the full Balmorel datetime axis
        # pivot_df = (
        #     full_datetime_axis[["DATETIME"]]
        #     .merge(
        #         pivot_df,
        #         on="DATETIME",
        #         how="left",
        #     )
        #     .sort_values("DATETIME")
        #     .fillna(0)
        # )

        value_df = pivot_df.drop(columns=["DATETIME"], errors="ignore")

        if value_df.empty:
            continue

        # Group small generation units into Other
        generation_totals = value_df.sum(axis=0)
        small_generators = generation_totals[generation_totals < min_value].index

        if len(small_generators) > 0:
            value_df["Other"] = value_df[small_generators].sum(axis=1)
            value_df = value_df.drop(columns=small_generators)

        # Remove columns that are entirely zero after grouping
        value_df = value_df.loc[:, value_df.sum(axis=0) > 0]

        if value_df.empty:
            continue

        # Sort generation units by total value
        value_df = value_df[
            value_df.sum(axis=0).sort_values(ascending=False).index
        ]

        # BIO* = green, everything else = blue
        colors = [
            "tab:green" if str(generator).strip().upper().startswith("BIO")
            else "tab:blue"
            for generator in value_df.columns
        ]

        x = pivot_df["DATETIME"]

        fig, ax = plt.subplots(figsize=(15, 6))

        # --- REPLACED STACKPLOT WITH STEPPED FILL_BETWEEN FOR SOLID COLORS ---
        y_stack = value_df.T.values
        y_cumulative = np.zeros(len(x))

        for i, col in enumerate(value_df.columns):
            y_next = y_cumulative + y_stack[i]
            ax.fill_between(
                x,
                y_cumulative,
                y_next,
                label=col,
                color=colors[i],
                step="mid",  # Ensures sharp, blocky, solid bars instead of thin triangles
                edgecolor="none",
                alpha=1.0,
                zorder=2,
                antialiased=False,
            )
            y_cumulative = y_next
        # --------------------------------------------------------------------

        title = f"Generation by Unit - {scenario} - {year}"
        if country is not None:
            title += f" - {country}"
        if region is not None:
            title += f" - {region}"
        if area is not None:
            title += f" - {area}"

        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_ylabel("Generation / Value (MWh)")
        ax.set_xlabel("Datetime")
        
        # --- NEW LINE ADDED TO FIX Y-AXIS LIMITS ---
        ax.set_ylim(0, 2000)
        # -------------------------------------------
        
        ax.grid(True, axis="y", alpha=0.3, zorder=0)

        # Monthly x-axis labels
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

        plt.setp(
            ax.get_xticklabels(),
            rotation=45,
            ha="right",
            fontsize=8,
        )

        ax.legend(
            title="Generation",
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=8,
        )

        plt.tight_layout()

        figures[scenario] = (fig, ax)

    return figures


generation_tech_color = {
    "HYDRO-RESERVOIRS": "#33b1ff",
    "HYDRO-RUN-OF-RIVER": "#4589ff",
    "HYDRO": "#33b1ff",
    "WIND-ONSHORE": "#006460",
    "BOILERS": "#8B008B",
    "ELECT-TO-HEAT": "#FFA500",
    "INTERSEASONAL-HEAT-STORAGE": "#FFD700",
    "CHP-BACK-PRESSURE": "#E5D8D8",
    "SMR-CCS": "#00BFFF",
    "SMR": "#d1b9b9",
    "INTRASEASONAL-HEAT-STORAGE": "#00FFFF",
    "CONDENSING": "#8a3ffc",
    "SOLAR-HEATING": "#FF69B4",
    "CHP-EXTRACTION": "#ff7eb6",
    "SOLAR-PV": "#d2a106",
    "WIND-OFFSHORE": "#08bdba",
    "INTRASEASONAL-ELECT-STORAGE": "#ba4e00",
    "ELECTROLYZER": "#ADD8E6",
    "H2-STORAGE": "#FFC0CB",
    "FUELCELL": "#d4bbff",
    "CHP": "#E5D8D8",
}

def plot_capacity_by_fuel(
    capacity_df: pd.DataFrame,
    year: int = None,
    scenarios: list = None,
    min_capacity: float = 0.0,
):
    df = capacity_df.copy()

    df["Scenario_clean"] = df["Scenario"].astype(str).str.strip()
    df["Fuel"] = df["Fuel"].astype(str).str.strip()
    df["Year"] = df["Year"].astype(int)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)

    if year is not None:
        df = df[df["Year"] == int(year)]

    if scenarios is not None:
        scenario_order = [str(s).strip() for s in scenarios]
        df = df[df["Scenario_clean"].isin(scenario_order)]
    else:
        scenario_order = sorted(df["Scenario_clean"].unique())

    agg = (
        df.groupby(["Scenario_clean", "Fuel"], as_index=False)["Value"]
        .sum()
    )

    agg = agg[agg["Value"] > min_capacity]

    pivot = agg.pivot_table(
        index="Scenario_clean",
        columns="Fuel",
        values="Value",
        aggfunc="sum",
        fill_value=0,
    )

    pivot = pivot.reindex(scenario_order).fillna(0)

    # Remove fuels with zero total after filtering
    pivot = pivot.loc[:, pivot.sum(axis=0) > 0]

    n = len(pivot)
    fig, ax = plt.subplots(figsize=(max(8, n * 1.4), 6))

    inds = np.arange(n)
    width = 0.55
    fuel_colors = [balmorel_colours.get(str(fuel).upper(), "#B0B0B0") for fuel in pivot.columns]

    for idx, sc in enumerate(pivot.index):
        bottom = 0

        for fuel, color in zip(pivot.columns, fuel_colors):
            val = pivot.at[sc, fuel]

            ax.bar(
                inds[idx],
                val,
                width,
                bottom=bottom,
                color=color,
            )
            bottom += val

    ax.set_xticks(inds)
    ax.set_xticklabels([str(s) for s in pivot.index], rotation=30, ha="right")

    ax.set_ylabel("Installed capacity (GW)")
    ax.set_title("Installed Capacity by Fuel" + (f" - {year}" if year is not None else ""))
    ax.grid(True, axis="y", alpha=0.3)

    legend_handles = [
        mpatches.Patch(color=color, label=str(fuel))
        for fuel, color in zip(pivot.columns, fuel_colors)
    ]
    if legend_handles:
        ax.legend(handles=legend_handles, title="Fuel", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout(rect=(0, 0, 0.84, 1))
    return fig, ax

def plot_renewables_vs_storage_by_tech(capacity_df: pd.DataFrame, year: int = None, scenarios: list = None, min_capacity: float = 0.0):
    df = capacity_df.copy()
    df["Scenario_clean"] = df["Scenario"].astype(str).str.strip()
    df["Year"] = df["Year"].astype(int)
    if year is not None:
        df = df[df["Year"] == int(year)]
    if scenarios is not None:
        keys = [str(s).strip() for s in scenarios]
        df = df[df["Scenario_clean"].isin(keys)]

    agg = df.groupby(["Scenario_clean", "Technology"])["Value"].sum().reset_index()
    agg = agg[agg["Value"] > 0]
    pivot = agg.pivot_table(index="Scenario_clean", columns="Technology", values="Value", aggfunc="sum", fill_value=0)
    if scenarios is not None:
        pivot = pivot.reindex([str(s).strip() for s in scenarios])

    # Identify renewables and storage technology columns
    renewable_keywords = ['wind','solar','pv','run','bio','biomass','geothermal']
    storage_keywords = ['storage','reservoir','interseasonal']

    renewable_cols = [c for c in pivot.columns if any(k in str(c).lower() for k in renewable_keywords)]
    storage_cols = [c for c in pivot.columns if any(k in str(c).lower() for k in storage_keywords)]

    # Fallback: if no explicit storage or renewables found, try some common names
    if not renewable_cols:
        renewable_cols = [c for c in pivot.columns if 'wind' in str(c).lower() or 'solar' in str(c).lower() or 'pv' in str(c).lower()]
    if not storage_cols:
        storage_cols = [c for c in pivot.columns if 'storage' in str(c).lower() or 'reservoir' in str(c).lower()]

    # Create figure
    n = len(pivot)
    fig, ax = plt.subplots(figsize=(max(8, n*1.4), 6))
    inds = np.arange(n)
    width = 0.35

    # Plot stacked bars for each scenario
    for idx, sc in enumerate(pivot.index):
        # Renewables stacked
        bottom_r = 0
        for tech in renewable_cols:
            val = pivot.at[sc, tech] if tech in pivot.columns else 0
            if val > 0:
                color = generation_tech_color.get(str(tech).strip().upper(), 'grey')
                ax.bar(inds[idx] - width/2, val, width, bottom=bottom_r, color=color)
                bottom_r += val
        # Storage stacked
        bottom_s = 0
        for tech in storage_cols:
            val = pivot.at[sc, tech] if tech in pivot.columns else 0
            if val > 0:
                color = generation_tech_color.get(str(tech).strip().upper(), 'grey')
                ax.bar(inds[idx] + width/2, val, width, bottom=bottom_s, color=color)
                bottom_s += val

    ax.set_xticks(inds)
    ax.set_xticklabels([str(s) for s in pivot.index], rotation=30, ha='right')
    ax.set_ylabel('Installed capacity (GW)')
    ax.set_title('Renewable Capacity vs Storage Energy by Scenario' + (f' - {year}' if year is not None else ''))
    ax.grid(True, axis='y', alpha=0.3)

    # Build legend with technology patches
    patches = []
    for tech in dict.fromkeys(list(renewable_cols) + list(storage_cols)):
        color = generation_tech_color.get(str(tech).strip().upper(), 'grey')
        patches.append(mpatches.Patch(color=color, label=tech))
    if patches:
        ax.legend(handles=patches, title='Technologies', bbox_to_anchor=(1.02,1), loc='upper left', fontsize=8)

    plt.tight_layout()
    return fig, ax


def plot_ccs_vs_renewables_by_co2price(
    capacity_df: pd.DataFrame,
    co2_prices: dict,
    year: int = None,
    scenarios: list = None,
    ccs_generators: list = None,
):
    """
    Plot CCS capacity vs Renewable capacity as a function of CO2 price.
    
    Args:
        capacity_df (pd.DataFrame): Installed capacity results dataframe.
        co2_prices (dict): Dictionary mapping scenario names to CO2 prices.
                           e.g. {'Net-Zero w CCS 87': 87, 'Net-Zero w CCS 174': 174, 'Net-Zero w CCS 250': 250}
        year (int, optional): Year to filter on.
        scenarios (list, optional): Scenarios to include (must match keys in co2_prices).
        ccs_generators (list, optional): Generator names from CCS_CCS_G to count as CCS capacity.
    
    Returns:
        tuple[plt.Figure, plt.Axes]: The figure and axes.
    """
    
    renewable_keywords = ['wind', 'solar', 'pv', 'hydro-run']

    df = capacity_df.copy()
    df["Scenario_clean"] = df["Scenario"].astype(str).str.strip()
    df["Year"] = df["Year"].astype(int)

    if year is not None:
        df = df[df["Year"] == int(year)]

    if scenarios is not None:
        df = df[df["Scenario_clean"].isin([str(s).strip() for s in scenarios])]

    df = df[df["Value"] > 0]

    if ccs_generators is None:
        raise ValueError("ccs_generators must be provided so CCS can be filtered by Generation.")

    if "Generation" not in df.columns:
        raise ValueError("Column 'Generation' is required to filter CCS generators.")

    ccs_generators_upper = {
        str(generator).strip().upper()
        for generator in ccs_generators
        if str(generator).strip()
    }

    # Identify renewable and CCS columns per scenario
    results = []
    for scenario, group in df.groupby("Scenario_clean"):
        if scenario not in co2_prices:
            continue

        renewable_cap = group[
            group["Technology"].str.lower().str.contains('|'.join(renewable_keywords), na=False)
        ]["Value"].sum()

        ccs_cap = group[
            group["Generation"].astype(str).str.strip().str.upper().isin(ccs_generators_upper)
        ]["Value"].sum()

        results.append({
            "Scenario": scenario,
            "CO2_price": co2_prices[scenario],
            "Renewable_GW": renewable_cap,
            "CCS_GW": ccs_cap,
        })

    if not results:
        raise ValueError("No matching scenarios found in co2_prices dictionary.")

    results_df = pd.DataFrame(results).sort_values("CO2_price")

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(9, 6))

    ax.plot(
        results_df["CO2_price"],
        results_df["Renewable_GW"],
        marker='o',
        linewidth=2,
        markersize=8,
        color="#d2a106",
        label="Renewable Capacity (GW)",
    )

    ax.plot(
        results_df["CO2_price"],
        results_df["CCS_GW"],
        marker='s',
        linewidth=2,
        markersize=8,
        color="#ff7eb6",
        label="CCS Capacity (GW)",
        linestyle='--',
    )

    # Annotate scenario names on points
    for _, row in results_df.iterrows():
        ax.annotate(
            row["Scenario"],
            xy=(row["CO2_price"], row["Renewable_GW"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            color="#d2a106",
        )
        ax.annotate(
            row["Scenario"],
            xy=(row["CO2_price"], row["CCS_GW"]),
            xytext=(5, -12),
            textcoords="offset points",
            fontsize=8,
            color="#ff7eb6",
        )


    ax.set_xlabel("CO₂ Price ($/tCO₂)", fontsize=12)
    ax.set_ylabel("Installed Capacity (GW)", fontsize=12)
    ax.set_title(
        f"CCS vs Renewable Capacity by CO₂ Price" + (f" — {year}" if year else ""),
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xticks([87, 174, 250])
    ax.set_xticklabels(["87\n(IEA Current\nPolicies)", "174\n(IEA Stated\nPolicies)", "250\n(IEA Net Zero)"])
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig, ax
# %%

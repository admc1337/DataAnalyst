
import requests
import pandas as pd
import time
import re  # For regular expressions to parse mana costs
import matplotlib.pyplot as plt  # For plotting
import seaborn as sns  # Import seaborn
import numpy as np  # For numerical operations (e.g., filtering zeros for plot)


def fetchData(cardname):
    """
    makes the api call to scryfall to get json data back
    """
    apiurl = "https://api.scryfall.com/cards/named"
    params = {"exact": cardname}

    try:
        response = requests.get(apiurl, params=params)
        response.raise_for_status()  # For error checking
        carddata = response.json()

        # Grabs all the data I want from the json file
        return {
            'name': carddata.get('name'),
            'color_identity': carddata.get('color_identity', []),
            'type_line': carddata.get('type_line'),
            'cmc': carddata.get('cmc')
        }
    # Returns error if failed (usually due to typo in card name)
    except requests.RequestException as error:
        print(f"Error fetching data for '{cardname}': {error}")
        return None


def analyzeDecklist(file):
    """
    Reads a text file, makes the api call for data and returns list
    of card dictionaries 
    """
    cardData = []
    with open(file, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            match = re.match(r'(\d+)\s+(.*)', line)
            if match:
                quantity = int(match.group(1))
                cardName = match.group(2).strip()
            else:
                quantity = 1
                cardName = line.strip()

            print(f"Processing: {cardName} (x{quantity})")
            data = fetchData(cardName)
            if data:
                data['quantity'] = quantity
                cardData.append(data)
            else:
                print(f"Skipping '{cardName} due to fetch error or not found")
            time.sleep(0.05)  # Scryfall asks to rate limit
    return cardData


def countColorIdentity(dataFrame):
    """
    Counts total color identity of the deck
    """
    colorCounts = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0}

    for index, row in dataFrame.iterrows():
        quantity = row['quantity']
        identity = row['color_identity']

        if not identity:
            if not (row['type_line'] and "Land" in row['type_line']):
                colorCounts['C'] += quantity
        else:
            for color in identity:
                if color in colorCounts:
                    colorCounts[color] += quantity
                else:
                    print(f"Warning: Unexpected color identity '{color}'")
    return colorCounts


# Kept old function due to finding out I could do this with Pandas function
'''
def countCMC(dataFrame):
    """
    Counts up how many cards per CMC slot
    """
    cmcCounts = {}

    for index, row in dataFrame.iterrows():
        cost = row['cmc']
        quantity = row['quantity']

        if pd.isna(cost) or cost is None:
            continue

        cmcSlot = int(cost)

        if cmcSlot not in cmcCounts:
            cmcCounts[cmcSlot] = 0
        cmcCounts[cmcSlot] += quantity

    return cmcCounts
'''


if __name__ == "__main__":
    decklist = "decklist.txt"
    allCardData = analyzeDecklist(decklist)

    if allCardData:
        df = pd.DataFrame(allCardData)

        if 'quantity' not in df.columns:
            print(f"Warning: 'quantity' not found in DataFrame, making all quantities 1")
            df['quantity'] = 1

        print("\n ---Card Data Test (first 5 rows)--- ")
        print(df.head())

        # splits the dataframe into two separate copies
        nonlandDf = df[~df['type_line'].str.contains('Land',
                                                     na=False)].copy()

        landDf = df[df['type_line'].str.contains('Land',
                                                 na=False)].copy()

        # Getting color identity based on all nonland cards
        deckColorIDCount = countColorIdentity(nonlandDf)
        print("\n ---Total Color Identity (per nonland card)--- ")
        filteredIDCount = {
            k: v for k, v in deckColorIDCount.items() if v > 0}
        print(filteredIDCount)

        # Calculates percentages of each color from nonland cards
        totalIDPoints = sum(filteredIDCount.values())
        if totalIDPoints > 0:
            IDPercentage = {
                k: (v / totalIDPoints) * 100 for k, v in filteredIDCount.items()}
            print("\n ---Color Identity Percentages--- ")
            print(IDPercentage)

        # Getting CMC per group in decklist

        # Learning Pandas functionality
        cmcDataSeries = nonlandDf.groupby('cmc')['quantity'].sum()
        cmcDict = cmcDataSeries.to_dict()
        print("\n ---Total CMC Costs Per Amount--- ")
        # Convert keys to int for plotting and readablity
        cmcIntDict = {int(k): v for k, v in cmcDict.items()}
        print(dict(sorted(cmcIntDict.items())))

    # ---Begining to do the data visualization here---

    sns.set_theme(style="darkgrid", palette="pastel")

    # Pie chart for color identity per nonland card
    if filteredIDCount:
        labels = filteredIDCount.keys()
        sizes = filteredIDCount.values()

        colorMap = {
            'W': '#F9FAF9', 'U': '#ADD8E6', 'B': '#36454F', 'R': '#DC143C', 'G': '#7CFC00',
            'C': '#A9A9A9'
        }

        plotColors = [colorMap.get(label, '#CCCCCC') for label in labels]

        plt.figure(figsize=(10, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plotColors,
                wedgeprops={'edgecolor': 'black', 'linewidth': 0.5},
                textprops={'fontsize': 12})
        plt.title(
            'Deck Color Identity Distribution (Per Nonland Card)', fontsize=16)
        plt.axis('equal')
        plt.show()

        # Bar chart for mana curve
        if not nonlandDf.empty:
            # Creates new Panda frame from cmcintdict
            manaCurveData = pd.DataFrame(
                list(cmcIntDict.items()), columns=['CMC', 'Count'])
            manaCurveData['CMC'] = pd.Categorical(manaCurveData['CMC'],
                                                  categories=sorted(
                                                      manaCurveData['CMC'].unique()),
                                                  ordered=True)
            manaCurveData = manaCurveData.sort_values('CMC')

            plt.figure(figsize=(12, 6))
            sns.barplot(x='CMC', y='Count', data=manaCurveData,
                        palette='coolwarm', edgecolor='black')
            plt.title(
                'Mana Curve (Converted Mana Cost Distribution of Spells)', fontsize=16)
            plt.xlabel('Converted Mana Cost (CMC)', fontsize=14)
            plt.ylabel('Number of Spells', fontsize=14)
            plt.xticks(rotation=0)
            plt.grid(axis='y', linestyle='--', alpha=0.7)  # Added grid back
            plt.tight_layout()
            plt.show()

        if totalIDPoints > 0:
            IDPercentagedf = pd.DataFrame([IDPercentage])

            orderedCol = [c for c in ['W', 'U', 'B', 'R',
                                      'G', 'C'] if c in IDPercentagedf.columns]
            IDPercentagedf = IDPercentagedf[orderedCol]

            currentPlotColors = [colorMap.get(
                col, '#CCCCCC') for col in IDPercentagedf.columns]

            plt.figure(figsize=(10, 4))  # Adjust figure size for a single bar
            # Plot as a stacked horizontal bar chart
            IDPercentagedf.plot(
                kind='barh',
                stacked=True,
                ax=plt.gca(),  # Get current axes to plot on
                color=currentPlotColors,
                edgecolor='black',
                linewidth=0.5
            )
            plt.title(
                'Color Identity Breakdown (Percentage of Total Identity)', fontsize=16)
            plt.xlabel('Percentage of Deck Color Identity', fontsize=14)
            plt.ylabel('')  # No y-label needed for a single stacked bar
            # Set x-ticks from 0-100 in steps of 10
            plt.xticks(np.arange(0, 101, 10))
            plt.xlim(0, 100)  # Ensure x-axis goes exactly from 0 to 100
            plt.legend(title='Color', bbox_to_anchor=(1.05, 1),
                       loc='upper left')  # Move legend outside
            plt.tight_layout()
            plt.show()
    else:
        print("No card data was fetched. Please check your decklist file and internet connection.")

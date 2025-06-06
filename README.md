This is my first data analysis project I wanted to do. I know the programs already exist for what I wanted to do, but I wanted to code from the ground up to understand how the data part of the code works. I like to play
a lot of commander in Magic The Gathering and one of the first things I look for when building a deck is the mana curve and the percentage of color of the deck. This data helps me build a mana base to work efficiently with
the deck.
How I went about this was I used Pandas and coded in Python. I made API calls to Scryfall's API with card names I get from the decklist.txt file I made. It goes through every line of the txt file and requests data by API
call with the string per line. It takes the API response (a JSON with the card data) and throws it into a dictionary that is then turned into a Panda DataFrame for later use. From there, I cleaned up the data and 
organized it for my needs, in this case card cost and color identity per nonland card. From there I printed out into the console the DataFrames to confirm it worked, then took the DataFrames and represented them as graphs
through matplotlib and seaborn. 
I learned a lot through this project, refreshed my skills on API calls and learned how to clean data and manipulate DataFrames.

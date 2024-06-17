import nest_asyncio
nest_asyncio.apply()
import discord
from discord.ext import commands
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.worksheet.dimensions import ColumnDimension
import requests
import math

intents = discord.Intents.default()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Function to calculate the battle score for a player
def get_battle_score(player):
    # Handle empty string values by replacing with 0
    score = 0
    for stat in ['strength', 'dexterity', 'defense', 'speed']:
        if stat in player and player[stat] != '':
            score += math.sqrt(float(player[stat]))
    return score

# Function to calculate the base respect based on level
def get_base_respect(level):
    base_respect = (1 / 198) * level + (197 / 198)
    if base_respect < 1:
        return 1
    elif base_respect > 1.5:
        return 1.5
    else:
        return base_respect

# Function to calculate the fair fight bonus based on defender and attacker scores
def get_fair_fight_bonus(defender_score, attacker_score):
    bonus_multiplier = 1 + (8 / 3) * (defender_score / attacker_score)
    return max(1, min(bonus_multiplier, 3))

# Function to fetch attacker stats using the Torn API
def fetch_attacker_stats(api_key):
    link_a = f"https://api.torn.com/user/?key={api_key}&comment=TornAPI&selections=battlestats"
    link_b = f"https://api.torn.com/user/?key={api_key}&comment=TornAPI&selections=profile"

    response_a = requests.get(link_a)
    response_b = requests.get(link_b)

    data_a = response_a.json()
    data_b = response_b.json()

    level = data_b.get('level')
    name = data_b.get('name')

    attacker = {
        'name': name,
        'level': level,
        'strength': data_a.get('strength'),
        'defense': data_a.get('defense'),
        'speed': data_a.get('speed'),
        'dexterity': data_a.get('dexterity'),
        'total_stats': data_a.get('strength', 0) + data_a.get('defense', 0) + data_a.get('speed', 0) + data_a.get('dexterity', 0)
    }

    return attacker

# Function to calculate respect for attackers against defenders
def calculate_respect(defenders, attackers, warlord_multiplier=1):
    results = []
    for attacker in attackers:
        attacker_score = get_battle_score(attacker)
        defender_respects = []
        for defender in defenders:
            defender_score = get_battle_score(defender)
            base_respect = get_base_respect(defender['level'])
            fair_fight_bonus = get_fair_fight_bonus(defender_score, attacker_score)

            total_respect = base_respect * fair_fight_bonus
            defender_respect = {
                'name': defender['name'],
                'level': defender['level'],
                'respect': total_respect,
                'total_stats': defender['total_stats'],
                'stats_ratio': defender['total_stats'] / attacker['total_stats'],  # Calculate the ratio
                'id': defender['id']  # Add 'id' field
            }
            defender_respects.append(defender_respect)
        results.append({'name': attacker['name'], 'defender_respects': defender_respects})
    return results

@bot.command(name='respect')
async def respect(ctx, api_key: str, warlord_multiplier: float):
    defenders = [{'name': 'Swaggie', 'id': '22299', 'level': 100, 'total_stats': 6292085554, 'strength': 1056556934, 'speed': 1319292107, 'dexterity': 1086918275, 'defense': 2829318238}, {'name': 'PirateDan', 'id': '22550', 'level': 98, 'total_stats': 2050355492, 'strength': 748834008, 'speed': 750603361, 'dexterity': 325167387, 'defense': 225750736}, {'name': 'Agent86', 'id': '13831', 'level': 86, 'total_stats': 2657261514, 'strength': 556084239, 'speed': 1000225960, 'dexterity': 1000027478, 'defense': 100923837}]
    attackers = [fetch_attacker_stats(api_key)]

    respect_results = calculate_respect(defenders, attackers, warlord_multiplier)

    # Create a DataFrame with the results
    data = []
    for result in respect_results:
        for defender_respect in result['defender_respects']:
            base_respect = defender_respect['respect']
            warlord_weapon_respect = warlord_multiplier * base_respect * 2
            avg_chain_respect = base_respect * warlord_multiplier * 1.24 * 2
            retaliation_respect = 1.5 * 1.24 * 2 * warlord_multiplier * base_respect

            data.append({
                'Goblin Name': result['name'],
                'Defender': defender_respect['name'],
                'Level': defender_respect['level'],
                'Total Stats': defender_respect['total_stats'],
                'Stats Ratio': round(defender_respect['stats_ratio'], 2),
                'FF and Base': round(base_respect * 2, 2),
                'Warlord': round(warlord_weapon_respect, 2),
                'Avg 1-2500th Chain': round(avg_chain_respect, 2),
                'Retaliation': round(retaliation_respect, 2),
                'id': defender_respect['id']
            })

    headers = ['Goblin Name', 'Defender', 'Level', 'Total Stats', 'Stats Ratio', 'FF and Base', 'Warlord', 'Avg 1-2500th Chain', 'Retaliation']
    message = ''
    for row in data:
        message += f"**{row['Goblin Name']}**\n"
        message += f"  - **{row['Defender']}** (Level {row['Level']})\n"
        message += f"    - Total Stats: {row['Total Stats']}\n"
        message += f"    - Stats Ratio: {row['Stats Ratio']:.2f}\n"
        message += f"    - FF and Base: {row['FF and Base']:.2f}\n"
        message += f"    - Warlord: {row['Warlord']:.2f}\n"
        message += f"    - Avg 1-2500th Chain: {row['Avg 1-2500th Chain']:.2f}\n"
        message += f"    - Retaliation: {row['Retaliation']:.2f}\n"
        message += "\n"

    await ctx.send(message)

bot.run('MTI0MTk0Nzk1NTQwMjExNzE3MA.GUCN9Z.kMLMZCDiQZmSErUgasvCq6UEnwObwkhqlXuZNI')

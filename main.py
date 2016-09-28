#!/usr/bin/env python

'''
Author: Zach Goins
Date: 05/01/2016
Email:zach.a.goins@gmail.com

'''
import numpy,math
from time import sleep
import threading
import sys
import logging
from coinbase.wallet.client import Client
import json

currency_code = 'USD'

# Turns logging on if you ever want it
logging.basicConfig(level=logging.INFO)

class Universe(object):

	''' A "universe" object that is used as a a middle man between whatever API ia used
		and the Wallet. The Universe objects starts a thread and constantly spins to update the
		fields of the dictionary. Then when anything wants the universe info it just calls the
		get method
	'''

	def __init__(self, api_key, api_secret, url):
		self.universe_info = {}
		self.universe_info['btc_buy_price'] = 1
		self.universe_info['btc_sell_price'] = 1
		self.universe_info['domestic_rate'] = 1
		# XXX API DOESNT ALLOW VOLUME ACCESS - GET IT HERE UPDATE DAILY -> https://coinmarketcap.com/exchanges/gdax/
		self.universe_info['volume'] = 2551630.0
		self.universe_info['ready'] = False

		self.wallets = []

		self.client = Client(api_key, api_secret, url)

		a = threading.Thread(target=self.get_universe_info)
		a.setDaemon(True); a.start()

	def get_universe(self):
		''' Return the data to whatever wants it
			Returns the entire dictionary.
		'''
		return self.universe_info

	def update_wallets_in_universe(self, new_wallet):
		logging.info("Adding New Wallet to Universe")
		logging.info(json.dumps(new_wallet, indent=4, sort_keys=True))
		self.wallets.append(new_wallet)

	def get_universe_info(self):
		''' This method will be used to update the dictionary fields. The while loop
			spins indefinitely and will eventually update data at a certain rate.
		'''

		while True:
			self.universe_info['btc_buy_price'] = self.client.get_buy_price(currency=currency_code)
			self.universe_info['btc_sell_price'] = self.client.get_sell_price(currency=currency_code)
			self.universe_info['domestic_rate'] = self.client.get_spot_price(currency=currency_code)
			self.universe_info['ready'] = True
			sleep(1)

class Wallet(object):

	''' A Wallet object contains all the methods necessary to make a new wallet and
		compute its weight and then listen for new orders and convert upon receipt.
		When the wallet is initiated its initial coin value is normalized.
		One thread is starts in this class to loop through and detect new orders.
	'''

	def __init__(self, api_key, api_secret, url):

		self.universe = Universe(api_key, api_secret, url)

		# All variables necessary for operation
		self.order_info = 0
		self.current_universe = 0
		self.exchange_rate = 0
		self.coins = 0
		self.current_volume = 0
		self.value = 0

		# Variables that are used to toggle when we want to make new wallets and orders
		self.new_order = True
		self.new_wallet = True

		# Thread to spin and listen for new orders
		a = threading.Thread(target=self.spin)
		a.setDaemon(True); a.start()

		# Get the current universe and normalize the original order
		self.current_universe = self.universe.get_universe()

	def spin(self):
		''' Spins indefinitely to update universe and convert new orders when they arrive.
		'''
		# update universe
		while True:
			self.current_universe = self.universe.get_universe()

			logging.info("UNIVERSE UPDATE")
			if self.current_universe['ready'] == True:
				logging.info(json.dumps(self.current_universe, indent=4, sort_keys=True))
			else:
				logging.info("Problem connecting to Coinbase Server - Can't update Universe")
				logging.info("All wallet activities halted")
			logging.info("New Wallet: " + str(self.new_wallet))
			logging.info("New Order: " + str(self.new_order))

			order = {} # XXX MUST BE FILLED IN BY GUI
			domestic_rate = self.current_universe['domestic_rate']
			btc_rate = self.current_universe['btc_buy_price']

			if self.new_order == True and self.current_universe['ready'] is True:
				logging.info("Placing New Order")
				# convert and then reset order flag
				self.converter(order, domestic_rate, btc_rate)
				self.new_order = False

			if self.new_wallet == True and self.current_universe['ready'] is True:
				logging.info("Creating New Wallet")
				# convert and then reset wallet flag
				coins = 10000.0 # XXX MUCH BE FILLED IN BY GUI
				self.make_new_wallet(coins)
				self.new_wallet = False

			sleep(1)

	def converter(self, order, domestic_rate, btc_rate):
		''' This function follows the flowcharts on the datasheet provided.
			Because the universe is updated in the spin() fuynction there is no need
			to grab it here. Sub-methods are called at the bottom of this function
		'''

		# Set order info as the params
		def order_info(order):
			self.order_info = order

		# get rates for universe
		def get_exhange_rate(domestic_rate, btc_rate):
			self.domestic_ex_rate = domestic_rate
			self.btc_ex_rate = btc_rate

		# If the btc rate is more than the domestic rate then the final rate is 1
		# else is a ratio of the two rates
		def find_weakest_currency():
			if self.domestic_ex_rate < self.btc_ex_rate:
				self.final_rate = 1
				logging.info("Domestic Rate is less than the BTC Rate")
			else:
				self.final_rate = 1/(self.domestic_ex_rate/self.btc_ex_rate)
				loggin.info("Domestic Rate is more than BTC, computing ratio")

			logging.info("Final Rate: " + str(self.final_rate))


		order_info(order)
		get_exhange_rate(domestic_rate, btc_rate)
		find_weakest_currency()

	def make_new_wallet(self, coins):
		''' This function follows the flowcharts on the datasheet provided.
			Sub-methods are called at the bottom of this function
		'''

		# Add coins to the wallet
		def add_coins_to_wallet(coins):
			self.coins = coins

		# Normalize the new wallet value as a function of its ratio to the universe volume
		def normalize_wallet():
			self.current_volume = self.current_universe['volume']
			self.wallet_weight = float(self.coins / self.current_volume)
			logging.info("Current Volume: " + str(self.current_volume))
			logging.info("Coins: " + str(self.coins))
			logging.info("Wallet Weight: " + str(self.wallet_weight))
			# Compute final value
			self.value = self.coins / self.wallet_weight

			logging.info("Current Value: " + str(self.value))

		add_coins_to_wallet(coins)
		normalize_wallet()

		new_wallet = {
				"value": self.value,
				"coins": self.coins,
				"weight:": self.wallet_weight
			}
		self.universe.update_wallets_in_universe(new_wallet)

if __name__ == "__main__":

	# FOR TESTING - make a new wallet to test normalize and converter data flow
	if len(sys.argv) == 4:
		wallet = Wallet(sys.argv[1], sys.argv[2], sys.argv[3])
	else:
		logging.info("Please run with the correct inputs")
		logging.info("FORMAT: python main.py api_key api_secret server_url")
		logging.info("EXAMPLE: python main.py wT1Ck5yzMpr JAxj7wlOGuOTr5tUYy https://api.sandbox.coinbase.com")

	# Loop until user exit
	while True:
		pass


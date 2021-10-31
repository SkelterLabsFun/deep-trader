# Deep Traders

This directory contains deep learning based stock trading system.

Design doc: https://docs.google.com/document/d/1TDrU1CxfyJ7QBZY_WBpRHaeVn7L3LtNp1viIoAfse70/edit#heading=h.e3nb2v558mw2

## Prerequisites

To execute this repo, we temporalily use virtualenv.

```bash
$ brew install pyenv
$ brew install pyenv-virtualenv
# Prepare required setting for pyenv
```

```bash
$ pyenv virtualenv 3.7.9 deeptraders
$ pyenv activate deeptraders
$ pip install -r requirements.txt
```

## Datasets

Gathered datasets are stored in the below paths:

* Trading data
    * Daily: `/nas0/home/jaesup.kwak/deep_traders/finance_data/2021-09-29/finance_data.tfrecord`
    * Minutes: `https://drive.google.com/file/d/1Y4SFQ9i-5M3NH5Y7RnWfFUPmKTtZEmmd/view?usp=sharing`

* Download new trading data
    * Daily: `python data/download_finance_data.py --outfile /your_path/finance_data.tfrecord`
    * Minutes: (TODO, use `data/download_chart_data.py`)

* Company data:
    * Origin: `/nas0/home/jaesup.kwak/deep_traders/financial_data.txt`
    * tfrecord: `/nas0/home/jaesup.kwak/deep_traders/financial_data.tfrecord`
    * Example format:
```
code	corp_name	year	total_equity	sales	profit	net_income	bps	per	eps	debt_ratio	profit_ratio
017960	한국카본	2020	3805	4117	757	574	8793	10.3	1305	25.7	18.4
017960	한국카본	2019	3127	2734	253	177	7532	19.45	403	27.14	9.25
017960	한국카본	2018	3037	2267	62	-30	7327	nan	-68	18.57	2.72
017960	한국카본	2017	3103	2391	58	7	7478	316.65	17	18.08	2.44
...
```

* Download new company data: (TODO, script is not exist)

## Usage

### Back test

To perform back test, execute the following command:

```bash
$ python back_tester.py
```

### Trading

To perform algorithm trading, you should execute two binaries.
1. trader
2. cybos_wrapper

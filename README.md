# Deep Traders

This directory contains deep learning based stock trading system.

Design doc: https://docs.google.com/document/d/1TDrU1CxfyJ7QBZY_WBpRHaeVn7L3LtNp1viIoAfse70/edit#heading=h.e3nb2v558mw2

## Prerequisites

To execute this repo, we temporalily use virtualenv.

```bash
$ pyenv virtualenv 3.7.9 deeptraders
$ pyenv activate deeptraders
$ pip install -r requirements.txt
```
## Datasets

Gathered datasets are stored in the below paths:

* Company data: `/nas0/home/jaesup.kwak/deep_traders/financial_data.txt`
* Trading data
    * Daily: `/nas0/home/jaesup.kwak/deep_traders/finance_data/2021-09-29/finance_data.tfrecord`
    * Minutes: `https://drive.google.com/file/d/1Y4SFQ9i-5M3NH5Y7RnWfFUPmKTtZEmmd/view?usp=sharing`

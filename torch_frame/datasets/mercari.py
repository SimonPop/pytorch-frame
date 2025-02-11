import os.path as osp
from typing import Optional

import pandas as pd

import torch_frame
from torch_frame.config.text_embedder import TextEmbedderConfig
from torch_frame.utils.split import SPLIT_TO_NUM

SPLIT_COL = 'split_col'


class Mercari(torch_frame.data.Dataset):
    r"""The `Mercari Price Suggestion Challenge
    <https://www.kaggle.com/c/mercari-price-suggestion-challenge/>`_
    dataset from Kaggle.

    **STATS:**

    .. list-table::
        :widths: 10 10 10 10 20 10
        :header-rows: 1

        * - #rows
          - #cols (numerical)
          - #cols (categorical)
          - #cols (text_embedded)
          - Task
          - Missing value ratio
        * - 1,482,535
          - 1
          - 4
          - 2
          - regression
          - 0.0%
    """
    base_url = 'https://data.pyg.org/datasets/tables/mercari_price_suggestion/'
    files = ['train', 'test_stg2']

    def __init__(self, root: str, num_rows: Optional[int] = None,
                 text_embedder_cfg: Optional[TextEmbedderConfig] = None):
        self.dfs = dict()
        col_to_stype = {
            'name': torch_frame.text_embedded,
            'item_condition_id': torch_frame.categorical,
            'category_name': torch_frame.multicategorical,
            'brand_name': torch_frame.categorical,
            'price': torch_frame.numerical,
            'shipping': torch_frame.categorical,
            'item_description': torch_frame.text_embedded,
        }
        train_path = osp.join(self.base_url, 'train.csv')
        self.download_url(train_path, root)
        df_train = pd.read_csv(train_path)
        test_path = osp.join(self.base_url, 'test_stg2.csv')
        self.download_url(test_path, root)
        df_test = pd.read_csv(test_path)
        df_train[SPLIT_COL] = SPLIT_TO_NUM['train']
        df_test[SPLIT_COL] = SPLIT_TO_NUM['test']
        df = pd.concat([df_train, df_test], axis=0, ignore_index=True)
        if num_rows is not None:
            df = df.head(num_rows)
        df.drop(['train_id'], axis=1, inplace=True)
        super().__init__(df, col_to_stype, target_col='price', col_to_sep="/",
                         text_embedder_cfg=text_embedder_cfg,
                         split_col=SPLIT_COL)

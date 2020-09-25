# time python3.6 prepare/splits.py --ext_images jpg \
# --path_input /data2/jose/corpus/tablas_DU/icdar_488/fold_1/train \
# --path_out /data2/jose/corpus/tablas_DU/icdar_488/fold_1/train_dev_data \
# --dev_split 0.1
time python3.6 prepare/splits.py --ext_images jpg \
--path_input /data2/jose/corpus/tablas_DU/icdar_488/fold_2/train \
--path_out /data2/jose/corpus/tablas_DU/icdar_488/fold_2/train_dev_data \
--dev_split 0.1
time python3.6 prepare/splits.py --ext_images jpg \
--path_input /data2/jose/corpus/tablas_DU/icdar_488/fold_3/train \
--path_out /data2/jose/corpus/tablas_DU/icdar_488/fold_3/train_dev_data \
--dev_split 0.1
time python3.6 prepare/splits.py --ext_images jpg \
--path_input /data2/jose/corpus/tablas_DU/icdar_488/fold_4/train \
--path_out /data2/jose/corpus/tablas_DU/icdar_488/fold_4/train_dev_data \
--dev_split 0.1
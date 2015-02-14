
update around_db.data_models_event set type_ext='0' where type='occupancy';
insert into around_db.data_models_log (user,function,message,timestamp) values ('batch','occupancy','set_to_zero batch',CURRENT_TIMESTAMP);

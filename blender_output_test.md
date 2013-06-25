%WRITE_FILENAME=blender_test.rib
%WRITE_PATH=/home/dankaczma/chronoman2/test/output/
%DATA_FILENAME=blender_test.dat
%DATA_PATH=/home/dankaczma/chronoman2/test/input/data/blender/
%DATA_FORMAT=ID,POS_X,POS_Y,POS_Z,QUAT_X,QUAT_Y,QUAT_Z,QUAT_W,ignore,ignore,ignore
%DELIM=,
%QUALITY=production
%PADDING=2
%SCALING_FACTOR=0.01
%RESOLUTION="320 240"
%PADDING=2
%CAMERA_POS="7.481131553649902 -6.5076398849487305 5.34366512298584"
%CAMERA_ROT="1.1093189716339111 1.1093189716339111 1.1093189716339111"
%INJECTIONRIB_SEARCHPATH=./:/home/dankaczma/chronoman2/test/input/injection_ribs:/home/dankaczma/chronoman2/share/injection_ribs/:/home/dankaczma/chronoman2/share/injection_ribs/cameras:/home/dankaczma/chronoman2/share/injection_ribs/lighting:/home/dankaczma/chronoman2/share/injection_ribs/passes:/home/dankaczma/chronoman2/share/injection_ribs/scenes:/home/dankaczma/chronoman2/share/injection_ribs/examples

ObjectBegin
%Name=Cube
%Range="1 2044"
%DATA_FORMAT=ID,POS_X,POS_Y,POS_Z,QUAT_X,QUAT_Y,QUAT_Z,QUAT_W,ignore,ignore,ignore
%Geometry = Cube 0.05 0.05 0.05
%color = "0.6 0.0 0.6"
Surface "plastic"
ObjectEnd

ObjectBegin
%Name=Sphere
%Range="2045 6052"
%DATA_FORMAT=ID,POS_X,POS_Y,POS_Z,QUAT_X,QUAT_Y,QUAT_Z,QUAT_W,ignore,ignore,ignore
%Geometry = Sphere 0.05
%color = "0.6 0.0 0.6"
Surface "plastic"
ObjectEnd

ObjectBegin
%Name=Ellipsoid
%Range="6053 8000"
%DATA_FORMAT=ID,POS_X,POS_Y,POS_Z,QUAT_X,QUAT_Y,QUAT_Z,QUAT_W,ignore,ignore,ignore
%Geometry = Ellipsoid 0.05 0.05
%color = "0.6 0.0 0.6"
Surface "plastic"
ObjectEnd
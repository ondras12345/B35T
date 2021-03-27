# B35T
Python library for interfacing with Owon B35T multimeter (BT2.0)

Owon do provide their own [app](https://www.owon.com.hk/products_owon_3_5%7C6_digital_multimeter_with_bluetooth) for the meter, but it only works on Android (there is a new Windows app, but it only works with the BLE4.0 version of the meter).

This library relies on the fact that Windows maps the DMM as a COM port when connected.
To make this work in GNU/Linux, try something like this:
```sh
sdptool add SP
rfcomm connect /dev/rfcomm0 00:11:22:33:44:55  # replace with your DMM's address
```
And then connect to `/dev/rfcomm0`.

I tested it with **Bluetooth 2.0** version of the DMM only because I don't own the BLE4.0 one.

This project is still **under development**. Anything can change at any time. If you find a bug, feel free to open an issue so that I can fix it.

For more info see the [wiki](https://github.com/ondras12345/B35T/wiki).

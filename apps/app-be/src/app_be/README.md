el flujo va asi
main -> service -> API_CLient

Imagina que hay un endpoint pagar
llega al main -> llama a servicio que se encarga de los pagos -> llama al API_CLinet que se encarga de llamar al STRIPE

SI en un futuro cambiabos de proveedor solo tenemos que cambiar API_CLient


las variables de entorno se cogen de config.env
los scripts son para tareas sencillas y cron etc
los utils son para cosas reutilizables como logger etc
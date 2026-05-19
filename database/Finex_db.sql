SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

SET FOREIGN_KEY_CHECKS = 0;
DROP TRIGGER IF EXISTS `trg_facturas_venta_ai_movimiento`;
DROP TRIGGER IF EXISTS `trg_facturas_venta_au_movimiento`;
DROP TRIGGER IF EXISTS `trg_facturas_venta_ad_movimiento`;
DROP TRIGGER IF EXISTS `trg_facturas_compra_ai_movimiento`;
DROP TRIGGER IF EXISTS `trg_facturas_compra_au_movimiento`;
DROP TRIGGER IF EXISTS `trg_facturas_compra_ad_movimiento`;
DROP TABLE IF EXISTS `movimientos_contables`;
DROP TABLE IF EXISTS `movimientos_persona`;
DROP TABLE IF EXISTS `cuentas_personales`;
DROP TABLE IF EXISTS `categorias`;
DROP TABLE IF EXISTS `factura_compra_items`;
DROP TABLE IF EXISTS `facturas_compra`;
DROP TABLE IF EXISTS `factura_venta_items`;
DROP TABLE IF EXISTS `facturas_venta`;
DROP TABLE IF EXISTS `items_venta`;
DROP TABLE IF EXISTS `proveedores`;
DROP TABLE IF EXISTS `clientes`;
DROP TABLE IF EXISTS `empresas`;
DROP TABLE IF EXISTS `personas`;
DROP TABLE IF EXISTS `usuarios`;
DROP TABLE IF EXISTS `extras_finex`;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(150) NOT NULL,
  `contraseña` varchar(255) DEFAULT NULL,
  `google_id` varchar(150) DEFAULT NULL,
  `microsoft_id` varchar(150) DEFAULT NULL,
  `foto` varchar(500) DEFAULT NULL,
  `tipo_cuenta` enum('persona','empresa') NOT NULL DEFAULT 'empresa',
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuarios_email` (`email`),
  UNIQUE KEY `uq_usuarios_google` (`google_id`),
  UNIQUE KEY `uq_usuarios_microsoft` (`microsoft_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `personas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `documento_identidad` varchar(80) NOT NULL,
  `telefono` varchar(30) NOT NULL,
  `direccion` varchar(180) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_personas_usuario` (`usuario_id`),
  CONSTRAINT `fk_personas_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `empresas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `nombre_contacto` varchar(100) NOT NULL,
  `razon_social` varchar(200) NOT NULL,
  `nombre_empresa` varchar(150) NOT NULL,
  `nit` varchar(50) NOT NULL,
  `tipo_empresa` varchar(30) DEFAULT NULL,
  `representante_legal` varchar(150) DEFAULT NULL,
  `telefono` varchar(30) NOT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `ciudad` varchar(100) NOT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `email_contacto` varchar(120) DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_empresas_usuario` (`usuario_id`),
  KEY `idx_empresas_nit` (`nit`),
  CONSTRAINT `fk_empresas_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `clientes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `tipo` enum('persona','empresa') DEFAULT 'empresa',
  `nombre` varchar(150) NOT NULL,
  `documento` varchar(50) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `telefono` varchar(30) DEFAULT NULL,
  `direccion` varchar(180) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `departamento` varchar(100) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_clientes_empresa` (`empresa_id`),
  KEY `idx_clientes_documento` (`documento`),
  CONSTRAINT `fk_clientes_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `proveedores` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `tipo` enum('persona','empresa') DEFAULT 'empresa',
  `nombre` varchar(150) NOT NULL,
  `numero_proveedor` varchar(80) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `telefono` varchar(30) DEFAULT NULL,
  `direccion` varchar(180) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_proveedores_empresa` (`empresa_id`),
  KEY `idx_proveedores_numero` (`numero_proveedor`),
  CONSTRAINT `fk_proveedores_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `items_venta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `tipo` enum('producto','servicio') NOT NULL DEFAULT 'servicio',
  `precio_unitario` decimal(14,0) NOT NULL DEFAULT 0,
  `cantidad` decimal(14,0) NOT NULL DEFAULT 0,
  `impuesto_porcentaje` decimal(5,0) NOT NULL DEFAULT 0,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_item_codigo_empresa` (`empresa_id`,`codigo`),
  KEY `idx_items_empresa` (`empresa_id`),
  CONSTRAINT `fk_items_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `facturas_venta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `cliente_id` int(11) NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `numero` varchar(50) NOT NULL,
  `fecha_emision` datetime NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `subtotal` decimal(14,0) NOT NULL DEFAULT 0,
  `impuestos` decimal(14,0) NOT NULL DEFAULT 0,
  `total` decimal(14,0) NOT NULL DEFAULT 0,
  `estado` enum('borrador','emitida','pagada','vencida','anulada') NOT NULL DEFAULT 'emitida',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ventas_numero_empresa` (`empresa_id`,`numero`),
  UNIQUE KEY `uq_ventas_codigo_empresa` (`empresa_id`,`codigo`),
  KEY `idx_ventas_cliente` (`cliente_id`),
  KEY `idx_ventas_empresa_fecha` (`empresa_id`,`fecha_emision`),
  CONSTRAINT `fk_ventas_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_ventas_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `factura_venta_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `factura_id` int(11) NOT NULL,
  `item_id` int(11) DEFAULT NULL,
  `descripcion` varchar(255) NOT NULL,
  `nota` varchar(255) DEFAULT NULL,
  `cantidad` decimal(14,0) NOT NULL DEFAULT 1,
  `precio_unitario` decimal(14,0) NOT NULL DEFAULT 0,
  `impuesto_porcentaje` decimal(5,0) NOT NULL DEFAULT 0,
  `subtotal` decimal(14,0) NOT NULL DEFAULT 0,
  `impuesto` decimal(14,0) NOT NULL DEFAULT 0,
  `total` decimal(14,0) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_venta_items_factura` (`factura_id`),
  KEY `idx_venta_items_item` (`item_id`),
  CONSTRAINT `fk_venta_items_factura` FOREIGN KEY (`factura_id`) REFERENCES `facturas_venta` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_venta_items_item` FOREIGN KEY (`item_id`) REFERENCES `items_venta` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `facturas_compra` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `proveedor_id` int(11) NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `numero` varchar(50) NOT NULL,
  `numero_proveedor` varchar(80) DEFAULT NULL,
  `fecha_emision` datetime NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `subtotal` decimal(14,0) NOT NULL DEFAULT 0,
  `impuestos` decimal(14,0) NOT NULL DEFAULT 0,
  `total` decimal(14,0) NOT NULL DEFAULT 0,
  `estado` enum('borrador','recibida','pagada','vencida','anulada') NOT NULL DEFAULT 'recibida',
  `observaciones` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_compras_numero_empresa` (`empresa_id`,`numero`),
  UNIQUE KEY `uq_compras_codigo_empresa` (`empresa_id`,`codigo`),
  KEY `idx_compras_proveedor` (`proveedor_id`),
  KEY `idx_compras_empresa_fecha` (`empresa_id`,`fecha_emision`),
  CONSTRAINT `fk_compras_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_compras_proveedor` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `factura_compra_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `factura_id` int(11) NOT NULL,
  `item_id` int(11) DEFAULT NULL,
  `descripcion` varchar(255) NOT NULL,
  `nota` varchar(255) DEFAULT NULL,
  `cantidad` decimal(14,0) NOT NULL DEFAULT 1,
  `valor_unitario` decimal(14,0) NOT NULL DEFAULT 0,
  `impuesto_porcentaje` decimal(5,0) NOT NULL DEFAULT 0,
  `subtotal` decimal(14,0) NOT NULL DEFAULT 0,
  `impuesto` decimal(14,0) NOT NULL DEFAULT 0,
  `total` decimal(14,0) NOT NULL DEFAULT 0,
  `categoria` varchar(100) DEFAULT 'Compra',
  PRIMARY KEY (`id`),
  KEY `idx_compra_items_factura` (`factura_id`),
  KEY `idx_compra_items_item` (`item_id`),
  CONSTRAINT `fk_compra_items_factura` FOREIGN KEY (`factura_id`) REFERENCES `facturas_compra` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_compra_items_item` FOREIGN KEY (`item_id`) REFERENCES `items_venta` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `categorias` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `tipo` enum('ingreso','egreso') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categoria_usuario_tipo_nombre` (`usuario_id`,`tipo`,`nombre`),
  CONSTRAINT `fk_categorias_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `cuentas_personales` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `tipo` enum('efectivo','banco','billetera','tarjeta') NOT NULL DEFAULT 'efectivo',
  `saldo_inicial` decimal(14,0) NOT NULL DEFAULT 0,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_cuentas_personales_usuario` (`usuario_id`),
  CONSTRAINT `fk_cuentas_personales_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `movimientos_persona` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `categoria_id` int(11) DEFAULT NULL,
  `cuenta_id` int(11) DEFAULT NULL,
  `tipo` enum('ingreso','egreso') NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `valor` decimal(14,0) NOT NULL DEFAULT 0,
  `fecha` datetime NOT NULL,
  `estado` enum('completado','vencido','anulado') NOT NULL DEFAULT 'completado',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_mov_persona_usuario_fecha` (`usuario_id`,`fecha`),
  KEY `idx_mov_persona_tipo` (`tipo`),
  KEY `idx_mov_persona_categoria` (`categoria_id`),
  KEY `idx_mov_persona_cuenta` (`cuenta_id`),
  CONSTRAINT `fk_mov_persona_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_mov_persona_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_mov_persona_cuenta` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_personales` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `movimientos_contables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_id` int(11) NOT NULL,
  `numero_movimiento` varchar(20) NOT NULL,
  `tipo` enum('ingreso','gasto') NOT NULL,
  `categoria` varchar(100) NOT NULL,
  `origen` enum('factura_venta','factura_compra') NOT NULL,
  `origen_id` int(11) NOT NULL,
  `factura_numero` varchar(50) NOT NULL,
  `fecha` datetime NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `valor` decimal(14,0) NOT NULL DEFAULT 0,
  `estado` varchar(40) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_movimiento_origen` (`origen`,`origen_id`),
  KEY `idx_mov_empresa_fecha` (`empresa_id`,`fecha`),
  KEY `idx_mov_tipo` (`tipo`),
  KEY `idx_mov_numero` (`numero_movimiento`),
  CONSTRAINT `fk_movimientos_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `extras_finex` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) DEFAULT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `datos` longtext DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DELIMITER $$
CREATE TRIGGER `trg_facturas_venta_ai_movimiento`
AFTER INSERT ON `facturas_venta`
FOR EACH ROW
BEGIN
  INSERT INTO `movimientos_contables`
    (`empresa_id`,`numero_movimiento`,`tipo`,`categoria`,`origen`,`origen_id`,`factura_numero`,`fecha`,`descripcion`,`valor`,`estado`,`created_at`)
  VALUES
    (NEW.empresa_id, NEW.codigo, 'ingreso', 'Venta', 'factura_venta', NEW.id, NEW.numero, NEW.fecha_emision,
     CONCAT('Factura de venta ', NEW.numero), NEW.total, NEW.estado, CURRENT_TIMESTAMP)
  ON DUPLICATE KEY UPDATE
    `numero_movimiento` = NEW.codigo,
    `tipo` = 'ingreso',
    `categoria` = 'Venta',
    `factura_numero` = NEW.numero,
    `fecha` = NEW.fecha_emision,
    `descripcion` = CONCAT('Factura de venta ', NEW.numero),
    `valor` = NEW.total,
    `estado` = NEW.estado,
    `updated_at` = CURRENT_TIMESTAMP;
END$$

CREATE TRIGGER `trg_facturas_venta_au_movimiento`
AFTER UPDATE ON `facturas_venta`
FOR EACH ROW
BEGIN
  INSERT INTO `movimientos_contables`
    (`empresa_id`,`numero_movimiento`,`tipo`,`categoria`,`origen`,`origen_id`,`factura_numero`,`fecha`,`descripcion`,`valor`,`estado`,`created_at`)
  VALUES
    (NEW.empresa_id, NEW.codigo, 'ingreso', 'Venta', 'factura_venta', NEW.id, NEW.numero, NEW.fecha_emision,
     CONCAT('Factura de venta ', NEW.numero), NEW.total, NEW.estado, CURRENT_TIMESTAMP)
  ON DUPLICATE KEY UPDATE
    `numero_movimiento` = NEW.codigo,
    `tipo` = 'ingreso',
    `categoria` = 'Venta',
    `factura_numero` = NEW.numero,
    `fecha` = NEW.fecha_emision,
    `descripcion` = CONCAT('Factura de venta ', NEW.numero),
    `valor` = NEW.total,
    `estado` = NEW.estado,
    `updated_at` = CURRENT_TIMESTAMP;
END$$

CREATE TRIGGER `trg_facturas_venta_ad_movimiento`
AFTER DELETE ON `facturas_venta`
FOR EACH ROW
BEGIN
  DELETE FROM `movimientos_contables`
  WHERE `origen` = 'factura_venta' AND `origen_id` = OLD.id;
END$$

CREATE TRIGGER `trg_facturas_compra_ai_movimiento`
AFTER INSERT ON `facturas_compra`
FOR EACH ROW
BEGIN
  INSERT INTO `movimientos_contables`
    (`empresa_id`,`numero_movimiento`,`tipo`,`categoria`,`origen`,`origen_id`,`factura_numero`,`fecha`,`descripcion`,`valor`,`estado`,`created_at`)
  VALUES
    (NEW.empresa_id, NEW.codigo, 'gasto', 'Compra', 'factura_compra', NEW.id, NEW.numero, NEW.fecha_emision,
     CONCAT('Factura de compra ', NEW.numero), NEW.total, NEW.estado, CURRENT_TIMESTAMP)
  ON DUPLICATE KEY UPDATE
    `numero_movimiento` = NEW.codigo,
    `tipo` = 'gasto',
    `categoria` = 'Compra',
    `factura_numero` = NEW.numero,
    `fecha` = NEW.fecha_emision,
    `descripcion` = CONCAT('Factura de compra ', NEW.numero),
    `valor` = NEW.total,
    `estado` = NEW.estado,
    `updated_at` = CURRENT_TIMESTAMP;
END$$

CREATE TRIGGER `trg_facturas_compra_au_movimiento`
AFTER UPDATE ON `facturas_compra`
FOR EACH ROW
BEGIN
  INSERT INTO `movimientos_contables`
    (`empresa_id`,`numero_movimiento`,`tipo`,`categoria`,`origen`,`origen_id`,`factura_numero`,`fecha`,`descripcion`,`valor`,`estado`,`created_at`)
  VALUES
    (NEW.empresa_id, NEW.codigo, 'gasto', 'Compra', 'factura_compra', NEW.id, NEW.numero, NEW.fecha_emision,
     CONCAT('Factura de compra ', NEW.numero), NEW.total, NEW.estado, CURRENT_TIMESTAMP)
  ON DUPLICATE KEY UPDATE
    `numero_movimiento` = NEW.codigo,
    `tipo` = 'gasto',
    `categoria` = 'Compra',
    `factura_numero` = NEW.numero,
    `fecha` = NEW.fecha_emision,
    `descripcion` = CONCAT('Factura de compra ', NEW.numero),
    `valor` = NEW.total,
    `estado` = NEW.estado,
    `updated_at` = CURRENT_TIMESTAMP;
END$$

CREATE TRIGGER `trg_facturas_compra_ad_movimiento`
AFTER DELETE ON `facturas_compra`
FOR EACH ROW
BEGIN
  DELETE FROM `movimientos_contables`
  WHERE `origen` = 'factura_compra' AND `origen_id` = OLD.id;
END$$
DELIMITER ;

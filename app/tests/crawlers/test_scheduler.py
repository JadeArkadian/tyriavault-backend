import asyncio
from unittest.mock import AsyncMock

import pytest

from app.crawlers.scheduler import CrawlerScheduler


@pytest.mark.asyncio
async def test_register_crawler():
    """Test que se puede registrar un crawler correctamente."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()

    scheduler.register_crawler("test_crawler", crawler_mock, interval_seconds=60)

    # Verificar que el crawler se registró
    assert "test_crawler" in scheduler._crawlers
    assert scheduler._crawlers["test_crawler"][0] == crawler_mock
    assert scheduler._crawlers["test_crawler"][1] == 60
    assert scheduler._crawlers["test_crawler"][2] == 300  # fail_interval por defecto


@pytest.mark.asyncio
async def test_register_multiple_crawlers():
    """Test que se pueden registrar múltiples crawlers."""
    scheduler = CrawlerScheduler()
    crawler1 = AsyncMock()
    crawler2 = AsyncMock()

    scheduler.register_crawler("crawler1", crawler1, interval_seconds=30)
    scheduler.register_crawler("crawler2", crawler2, interval_seconds=60, fail_interval_seconds=120)

    # Verificar que ambos crawlers se registraron
    assert len(scheduler._crawlers) == 2
    assert "crawler1" in scheduler._crawlers
    assert "crawler2" in scheduler._crawlers
    assert scheduler._crawlers["crawler2"][2] == 120


@pytest.mark.asyncio
async def test_start_all_creates_tasks():
    """Test que start_all crea tareas para todos los crawlers registrados."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()
    crawler_mock.crawl = AsyncMock()

    scheduler.register_crawler("test_crawler", crawler_mock, interval_seconds=1)

    # Iniciar el scheduler
    await scheduler.start_all()

    # Verificar que se creó una tarea
    assert "test_crawler" in scheduler._tasks
    assert isinstance(scheduler._tasks["test_crawler"], asyncio.Task)

    # Limpiar
    await scheduler.stop_all()


@pytest.mark.asyncio
async def test_crawler_executes_periodically():
    """Test que el crawler se ejecuta periódicamente según el intervalo."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()
    crawler_mock.crawl = AsyncMock()

    # Registrar con un intervalo muy corto para el test (1 segundo)
    scheduler.register_crawler("test_crawler", crawler_mock, interval_seconds=1)

    # Iniciar el scheduler
    await scheduler.start_all()

    # Esperar un poco para que se ejecute varias veces
    await asyncio.sleep(3)

    # Detener el scheduler
    await scheduler.stop_all()

    # Verificar que crawl se llamó al menos 2-3 veces
    assert crawler_mock.crawl.await_count >= 2


@pytest.mark.asyncio
async def test_crawler_handles_exceptions():
    """Test que el scheduler maneja excepciones del crawler y reintenta."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()

    # Hacer que el crawler falle las primeras 2 veces y luego tenga éxito
    call_count = 0

    async def failing_crawl():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Test error")

    crawler_mock.crawl = AsyncMock(side_effect=failing_crawl)

    # Registrar con intervalos cortos para el test (1 segundo)
    scheduler.register_crawler("test_crawler", crawler_mock,
                               interval_seconds=1,
                               fail_interval_seconds=1)

    # Iniciar el scheduler
    await scheduler.start_all()

    # Esperar a que se ejecute varias veces
    await asyncio.sleep(4)

    # Detener el scheduler
    await scheduler.stop_all()

    # Verificar que crawl se llamó múltiples veces a pesar de los errores
    assert crawler_mock.crawl.await_count >= 3


@pytest.mark.asyncio
async def test_stop_all_cancels_tasks():
    """Test que stop_all cancela todas las tareas del scheduler."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()
    crawler_mock.crawl = AsyncMock()

    scheduler.register_crawler("crawler1", crawler_mock, interval_seconds=10)
    scheduler.register_crawler("crawler2", crawler_mock, interval_seconds=10)

    # Iniciar el scheduler
    await scheduler.start_all()

    # Verificar que hay tareas
    assert len(scheduler._tasks) == 2

    # Detener el scheduler
    await scheduler.stop_all()

    # Verificar que las tareas se limpiaron
    assert len(scheduler._tasks) == 0


@pytest.mark.asyncio
async def test_multiple_crawlers_run_independently():
    """Test que múltiples crawlers se ejecutan de forma independiente."""
    scheduler = CrawlerScheduler()
    crawler1 = AsyncMock()
    crawler1.crawl = AsyncMock()
    crawler2 = AsyncMock()
    crawler2.crawl = AsyncMock()

    # Registrar con intervalos diferentes (1 y 3 segundos)
    scheduler.register_crawler("fast_crawler", crawler1, interval_seconds=1)
    scheduler.register_crawler("slow_crawler", crawler2, interval_seconds=3)

    # Iniciar el scheduler
    await scheduler.start_all()

    # Esperar
    await asyncio.sleep(5)

    # Detener el scheduler
    await scheduler.stop_all()

    # El crawler rápido debería haberse ejecutado más veces que el lento
    assert crawler1.crawl.await_count > crawler2.crawl.await_count


@pytest.mark.asyncio
async def test_crawler_uses_fail_interval_on_error():
    """Test que el crawler usa fail_interval cuando hay error."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()

    execution_times = []

    async def crawl_with_timing():
        import time
        execution_times.append(time.time())
        raise Exception("Test error")

    crawler_mock.crawl = AsyncMock(side_effect=crawl_with_timing)

    # Intervalo normal: 10s, intervalo de fallo: 1s
    scheduler.register_crawler("test_crawler", crawler_mock,
                               interval_seconds=10,
                               fail_interval_seconds=1)

    await scheduler.start_all()
    await asyncio.sleep(3.5)
    await scheduler.stop_all()

    # Debería haberse ejecutado al menos 3 veces con el fail_interval corto
    assert len(execution_times) >= 3

    # Verificar que el intervalo entre ejecuciones es cercano a 1s
    if len(execution_times) >= 2:
        interval = execution_times[1] - execution_times[0]
        assert 0.8 < interval < 1.5  # Permitir algo de variación


@pytest.mark.asyncio
async def test_empty_scheduler_start_stop():
    """Test que start_all y stop_all funcionan con un scheduler vacío."""
    scheduler = CrawlerScheduler()

    # No debería fallar aunque no haya crawlers registrados
    await scheduler.start_all()
    assert len(scheduler._tasks) == 0

    await scheduler.stop_all()
    assert len(scheduler._tasks) == 0

# Modem

DVB-S2 modem models — ModCod tables, performance curves, ACM policies, and throughput computation.

## Modem Model

::: opensatcom.modem.modem.ModemModel

## DVB-S2 Built-in Tables

::: opensatcom.modem.dvbs2
    options:
      members:
        - get_dvbs2_modcod_table
        - get_dvbs2_performance_curves

## Performance Curves

::: opensatcom.modem.curves.TablePerformanceCurve

::: opensatcom.modem.analytic_curves.AnalyticBERCurve

## ACM Policy

::: opensatcom.modem.acm.HysteresisACMPolicy

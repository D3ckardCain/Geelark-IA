# Inventario inicial de licencias y coste — Geelark-IA

**Fecha:** 2026-10-09  
**Estado:** evaluación preliminar de componentes principales. No sustituye el inventario automático de dependencias transitivas ni la revisión legal de las imágenes/aplicaciones redistribuidas.

## Criterios
- Sin cuota obligatoria, tarjeta ni prueba temporal.
- Preferir MIT, Apache-2.0, BSD, PostgreSQL License o dominio público.
- No asumir que “código abierto” significa que imágenes, APK, marcas o contenido se pueden redistribuir.
- Fijar versiones y lockfiles; registrar licencias transitivas antes de cada release.

## Componentes

| Componente | Uso previsto | Licencia/evidencia pública | Evaluación de coste | Decisión |
|---|---|---|---|---|
| Tauri 2 | Aplicación escritorio | MIT y MIT/Apache-2.0 según componente: https://github.com/tauri-apps/tauri | Sin cuota de licencia; hay que revisar cada plugin | Aprobado como candidato |
| React | UI | MIT: https://github.com/facebook/react/blob/main/LICENSE | Sin cuota de licencia | Candidato aprobado |
| Vite | Herramientas de frontend | MIT: https://github.com/vitejs/vite/blob/main/LICENSE | Sin cuota de licencia | Candidato aprobado |
| Python | Backend | Distribución disponible gratuitamente; términos PSF: https://www.python.org/psf/about/legal-and-policies/ | Sin cuota de licencia | Candidato aprobado |
| FastAPI | API local | MIT: https://github.com/fastapi/fastapi | Sin cuota de licencia | Candidato aprobado |
| SQLite | Persistencia local | Dominio público: https://www.sqlite.org/copyright.html | Sin cuota de licencia/servidor | Candidato aprobado |
| Android Emulator/SDK | Baseline Android | Condiciones del SDK de Google: https://developer.android.com/studio/terms | No asumir redistribución irrestricta; aceptar términos al descargar y revisar distribución de imágenes | Solo herramienta de desarrollo/prueba hasta revisar |
| redroid | Motor Android en contenedores | Repositorio/documentación pública: https://github.com/remote-android/redroid-doc | Sin cuota de uso indicada en el proyecto; revisar licencia exacta de cada imagen y componentes AOSP | Candidato experimental, no aprobado todavía |
| Waydroid | Alternativa Android Linux | Documentación y repositorio: https://github.com/waydroid/docs | Revisar licencias de imágenes/componentes | Alternativa experimental |
| Appium | Automatización de pruebas Android | Apache-2.0: https://github.com/appium/appium | Sin cuota de licencia | Herramienta de pruebas |
| Playwright | Pruebas E2E de UI | Proyecto público y aviso de licencia: https://github.com/microsoft/playwright | Sin cuota de licencia; revisar dependencias y navegadores instalados | Herramienta de pruebas |
| n8n | Motor general de workflows | Sustainable Use License y licencia Enterprise: https://docs.n8n.io/sustainable-use-license/ | Restricciones para ofrecer editor/automatización en un producto | No usar como motor integrado |
| GitHub Actions | CI opcional | Cuotas y condiciones de GitHub pueden cambiar: https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions | No puede ser requisito único; build local obligatorio | Opcional |

## Riesgos de licencia a vigilar
1. La licencia de la aplicación Android y la licencia de la imagen/sistema Android son asuntos distintos.
2. No redistribuir Google Play Services, Play Store, APK de terceros ni imágenes propietarias sin permiso explícito.
3. Mantener un SBOM (Software Bill of Materials) y archivo de licencias por release.
4. Generar una lista de licencias transitivas desde lockfiles; revisar excepciones y avisos.
5. No incorporar herramientas de automatización cuya licencia impida el uso previsto.
6. El coste cero de licencias no significa coste cero de electricidad, hardware, internet o mantenimiento.

## Validación previa a distribuir
- [ ] Fijar versiones exactas y lockfiles.
- [ ] Generar SBOM para frontend y backend.
- [ ] Generar lista de licencias de dependencias transitivas.
- [ ] Revisar licencias del motor y de cada imagen Android.
- [ ] Revisar redistribución de APK, Google components, codecs y fuentes.
- [ ] Confirmar que se puede compilar localmente sin GitHub Actions.
- [ ] Documentar servicios externos y confirmar que ninguno es obligatorio.

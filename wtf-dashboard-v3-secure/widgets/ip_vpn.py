import httpx
from textual.widgets import Static


class IpVpnWidget(Static):
    """Shows current public IP, ISP, location, and VPN/proxy detection."""

    DEFAULT_CSS = """
    IpVpnWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
    }
    IpVpnWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]IP / VPN STATUS[/]\n\n[#666666]Loading...[/]")
        self.set_interval(60, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            r = httpx.get("https://ipwho.is/", timeout=10)
            r.raise_for_status()
            d = r.json()

            ip = d.get("ip", "?")
            conn = d.get("connection", {})
            isp = (conn.get("isp") or d.get("org") or "?")[:24]
            city = d.get("city", "?")
            country = d.get("country_code", "?")

            security = d.get("security", {})
            is_proxy = security.get("proxy", False)
            is_vpn = security.get("vpn", False)
            vpn_status = is_proxy or is_vpn
            vpn_color = "#f87171" if vpn_status else "#4ade80"
            vpn_label = "Yes" if vpn_status else "No"

            text = (
                f"[bold #888888]IP / VPN STATUS[/]\n\n"
                f"[#666666]IP :[/]  [bold white]{ip}[/]\n"
                f"[#666666]ISP:[/]  [white]{isp}[/]\n"
                f"[#666666]VPN:[/]  [{vpn_color}]{vpn_label}[/]\n"
                f"[#666666]Loc:[/]  [white]{city}, {country}[/]"
            )
            self.app.call_from_thread(self.update, text)
        except (httpx.HTTPError, KeyError, ValueError) as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]IP / VPN STATUS[/]\n\n[#f87171]Error: {e}[/]"
            )

import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/** Editorial palette directions, not a calibrated cosmetic shade matcher. */
public class ShadeService {
    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(System.getenv().getOrDefault("GLOWSYNC_JAVA_PORT", "8081"));
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", port), 0);
        server.createContext("/health", exchange -> {
            byte[] body = "{\"status\":\"ok\"}".getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
            exchange.sendResponseHeaders(200, body.length);
            try (var out = exchange.getResponseBody()) { out.write(body); }
        });
        server.createContext("/palette", exchange -> {
            Map<String,String> q = new HashMap<>();
            String query = exchange.getRequestURI().getRawQuery();
            if (query != null) for (String pair : query.split("&")) {
                String[] p = pair.split("=", 2);
                if (p.length == 2) q.put(p[0], URLDecoder.decode(p[1], StandardCharsets.UTF_8));
            }
            boolean warm = q.getOrDefault("undertone", "neutral").equals("warm");
            boolean cool = q.getOrDefault("undertone", "neutral").equals("cool");
            boolean bold = q.getOrDefault("occasion", "everyday").matches("evening|festive");
            String lip = warm ? (bold ? "#A84735" : "#B77460") : cool ? (bold ? "#802D58" : "#B16E85") : (bold ? "#A63E55" : "#B27B78");
            String cheek = warm ? "#CD866D" : cool ? "#BE7D93" : "#C38A80";
            String eye = warm ? "#8C6545" : cool ? "#76627C" : "#8B7566";
            String fabric = switch(q.getOrDefault("clothing", "neutral")) {
                case "red" -> "#A63D46"; case "blue" -> "#536D9B";
                case "green" -> "#668273"; case "pink" -> "#BD819C";
                case "black" -> "#303035"; case "white" -> "#EEEAE2";
                default -> "#B8A693";
            };
            String direction = warm ? "Peach, terracotta and bronze" : cool ? "Rose, berry and soft plum" : "Rosewood, balanced pinks and taupe";
            String intensity = bold ? "Use one stronger focal point for your evening or festive look." : "Build soft layers for an everyday look.";
            String json = "{\"direction\":\"" + direction + "\",\"guidance\":\"" + intensity + "\",\"colours\":["
                + "{\"label\":\"Lip inspiration\",\"hex\":\"" + lip + "\"},"
                + "{\"label\":\"Cheek inspiration\",\"hex\":\"" + cheek + "\"},"
                + "{\"label\":\"Eye inspiration\",\"hex\":\"" + eye + "\"},"
                + "{\"label\":\"Outfit palette\",\"hex\":\"" + fabric + "\"}]}";
            byte[] body = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
            exchange.sendResponseHeaders(200, body.length);
            try (var out = exchange.getResponseBody()) { out.write(body); }
        });
        server.setExecutor(null);
        server.start();
        System.out.println("GlowSync shade service: 127.0.0.1:" + port);
    }
}

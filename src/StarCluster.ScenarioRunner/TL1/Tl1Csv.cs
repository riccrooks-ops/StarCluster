using System.Text;

namespace StarCluster.ScenarioRunner.TL1;

internal static class Tl1Csv
{
    public static IReadOnlyList<IReadOnlyList<string>> Read(string path)
    {
        if (!File.Exists(path))
        {
            throw new FileNotFoundException("CSV file was not found.", path);
        }

        string text = File.ReadAllText(path, Encoding.UTF8);
        if (text.Length > 0 && text[0] == '\uFEFF')
        {
            text = text[1..];
        }

        var rows = new List<IReadOnlyList<string>>();
        var row = new List<string>();
        var field = new StringBuilder();
        bool quoted = false;
        for (int index = 0; index < text.Length; index++)
        {
            char current = text[index];
            if (quoted)
            {
                if (current == '"')
                {
                    if (index + 1 < text.Length && text[index + 1] == '"')
                    {
                        field.Append('"');
                        index++;
                    }
                    else
                    {
                        quoted = false;
                    }
                }
                else
                {
                    field.Append(current);
                }
                continue;
            }

            if (current == '"' && field.Length == 0)
            {
                quoted = true;
            }
            else if (current == ',')
            {
                row.Add(field.ToString());
                field.Clear();
            }
            else if (current == '\r')
            {
                if (index + 1 < text.Length && text[index + 1] == '\n')
                {
                    index++;
                }
                CompleteRow(rows, row, field);
            }
            else if (current == '\n')
            {
                CompleteRow(rows, row, field);
            }
            else
            {
                field.Append(current);
            }
        }

        if (quoted)
        {
            throw new InvalidOperationException(
                $"CSV file '{path}' ended inside a quoted field.");
        }
        if (field.Length > 0 || row.Count > 0)
        {
            CompleteRow(rows, row, field);
        }
        return rows.AsReadOnly();
    }

    private static void CompleteRow(
        ICollection<IReadOnlyList<string>> rows,
        List<string> row,
        StringBuilder field)
    {
        row.Add(field.ToString());
        field.Clear();
        if (row.Any(value => value.Length > 0))
        {
            rows.Add(row.ToArray());
        }
        row.Clear();
    }
}

import { TFunction } from "i18next";
import Link from "next/link";
import { Trans } from "react-i18next/TransWithoutContext";

import { AuthorsLinks } from "@/app/components/AuthorsLinks";
import { MempoolPost, MempoolSeries } from "@/lib/api/schemas/mempool";
import { urls } from "@/lib/urls";
import { formatDate } from "@/utils/dates";

type SeriesHeaderProps = {
  t: TFunction<string, string>;
  locale: Locale;
  series: MempoolSeries;
  seriesIndex: number;
};

async function SeriesHeader({
  t,
  locale,
  series,
  seriesIndex,
}: SeriesHeaderProps) {
  return (
    <div className="mb-6">
      <h2 className="text-3xl">
        <Link href={urls(locale).mempool.seriesDetail(series.slug)}>
          {series.title}
        </Link>
        {!series.chapterTitle ? ` (#${seriesIndex})` : null}
      </h2>
      {series?.chapterTitle ? (
        <p className="text-3xl">
          <Trans
            t={t}
            i18nKey="chapter_index"
            values={{ index: seriesIndex }}
          />
        </p>
      ) : null}
    </div>
  );
}

type PostHeaderProps = {
  t: TFunction<string, string>;
  locale: Locale;
  post: MempoolPost;
};

export async function PostHeader({ t, locale, post }: PostHeaderProps) {
  return (
    <>
      <header className="mt-17 mx-auto max-w-4xl text-center">
        {post.series && post.seriesIndex !== null ? (
          <SeriesHeader
            t={t}
            locale={locale}
            series={post.series}
            seriesIndex={post.seriesIndex}
          />
        ) : null}
        <h1 className="mb-6 text-7xl font-medium">{post.title}</h1>
        <p className="text-2xl font-medium">
          <Trans
            t={t}
            i18nKey="by_authors"
            components={{
              authors: (
                <AuthorsLinks
                  as={"span"}
                  locale={locale}
                  authors={post.authors}
                />
              ),
            }}
          />
        </p>
        <p className="text-xl font-medium italic opacity-60">
          <time dateTime={post.date.toISOString()}>
            {formatDate(locale, post.date)}
          </time>
        </p>
        {post.originalUrl && post.originalUrl ? (
          <p className="mt-4 text-lg italic">
            <Trans
              t={t}
              i18nKey="first_published"
              values={{ originalSite: post.originalSite }}
              components={{
                em: <em className="not-italic" />,
                a: <Link href={post.originalUrl} />,
              }}
            />
          </p>
        ) : null}
        {post.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            className="mx-auto block rounded-sm pt-6 max-w-[640px]"
            src={post.image}
            alt={post.imageAlt ?? ""}
          />
        ) : null}
      </header>
      <hr className="mx-auto my-12 w-12 border border-opacity-40" />
    </>
  );
}
